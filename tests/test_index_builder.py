import asyncio
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import fakeredis
import pytest
from pydantic import BaseModel

from cacher import (
    AsyncIndex,
    DictSerializer,
    Index,
    IntSerializer,
    build_async_index,
    build_index,
    get_async_index,
    get_index,
)
from cacher.engines.async_redis_hash_engine import AsyncRedisHashEngine
from cacher.engines.engine import Engine
from cacher.engines.redis_hash_engine import RedisHashEngine
from cacher.engines.redis_string_engine import RedisStringEngine
from cacher.serializers.dataclass_serializer import DataclassSerializer
from cacher.serializers.datetime_serializer import DatetimeSerializer
from cacher.serializers.pydantic_serializer import PydanticSerializer
from cacher.serializers.serializer import Serializer

USER_ID = UUID("12345678-1234-5678-1234-567812345678")
MOMENT = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


class User(BaseModel):
    id: int
    name: str


class OtherUser(BaseModel):
    id: int
    name: str


class UserSerializer(PydanticSerializer[User]):
    """Specialized serializer. Its value type is ``User``, not the open type variable."""


class ActivitySerializer(DatetimeSerializer):
    """Concrete serializer subclass with no type arguments of its own."""


class Color:
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Color) and self.name == other.name


class ColorSerializer(Serializer[Color, str]):
    def serialize(self, value: Color) -> str:
        return value.name

    def deserialize(self, value: str) -> Color:
        return Color(value)


class NeedsExtra(Serializer[int, str]):
    def __init__(self, model: type[int], extra: int) -> None:
        self.model = model
        self.extra = extra

    def serialize(self, value: int) -> str:
        return str(value)

    def deserialize(self, value: str) -> int:
        return int(value)


class MemoryEngine(Engine[str, str]):
    def __init__(self) -> None:
        self.data: dict[tuple[str, str], str] = {}

    def get(self, name: str, field: str) -> str | None:
        return self.data.get((name, field))

    def set(self, name: str, field: str, value: str, *, ttl: int | None = None) -> None:
        self.data[(name, field)] = value

    def delete(self, name: str, field: str) -> None:
        self.data.pop((name, field), None)

    def exists(self, name: str, field: str) -> bool:
        return (name, field) in self.data

    def mget(self, name: str, fields: Sequence[str]) -> list[str | None]:
        return [self.data.get((name, field)) for field in fields]

    def mset(self, name: str, items: Mapping[str, str], *, ttl: int | None = None) -> None:
        for field, value in items.items():
            self.data[(name, field)] = value


class BytesEngine(Engine[str, bytes]):
    pass


class UuidFieldEngine(Engine[UUID, str]):
    pass


def test_builders_are_public() -> None:
    import cacher

    assert cacher.build_index is build_index
    assert cacher.build_async_index is build_async_index


def test_sync_datetime_index_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    index_cls = build_index(
        "user_last_activities",
        id_type=UUID,
        model_type=datetime,
        serializer=DatetimeSerializer,
        engine=RedisStringEngine,
    )

    assert index_cls is get_index("user_last_activities")
    assert issubclass(index_cls, Index)
    assert index_cls.identifier is UUID
    assert index_cls.model is datetime
    assert index_cls.key == "user_last_activities"
    assert index_cls.engine is RedisStringEngine
    assert isinstance(index_cls.serializer, DatetimeSerializer)

    engine = RedisStringEngine(client)
    index = index_cls(engine)
    assert isinstance(index, Index)
    assert index.engine is engine
    assert index_cls.engine is RedisStringEngine

    assert index.get(USER_ID) is None
    index.set(USER_ID, MOMENT)
    assert client.get(f"user_last_activities:{USER_ID}") == MOMENT.isoformat()
    assert index.get(USER_ID) == MOMENT

    with pytest.raises(TypeError):
        index_cls(RedisHashEngine(client))


def test_async_pydantic_index_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        index_cls = build_async_index(
            "builder_users",
            id_type=UUID,
            model_type=User,
            serializer=PydanticSerializer,
            engine=AsyncRedisHashEngine,
        )
        assert index_cls is get_async_index("builder_users")
        assert issubclass(index_cls, AsyncIndex)
        assert index_cls.identifier is UUID
        assert index_cls.model is User
        assert index_cls.engine is AsyncRedisHashEngine
        assert isinstance(index_cls.serializer, PydanticSerializer)

        engine = AsyncRedisHashEngine(client)
        index = index_cls(engine)
        user = User(id=1, name="Ada")
        try:
            assert isinstance(index, AsyncIndex)
            assert index.engine is engine
            await index.set(USER_ID, user)
            stored = await client.hget("builder_users", str(USER_ID))
            assert stored == user.model_dump_json()
            assert await index.get(USER_ID) == user
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_serializer_subclass_keeps_parent_types() -> None:
    index_cls = build_index(
        "builder_activity_subclass",
        id_type=UUID,
        model_type=datetime,
        serializer=ActivitySerializer,
        engine=RedisStringEngine,
    )
    assert isinstance(index_cls.serializer, ActivitySerializer)
    assert index_cls.model is datetime


def test_custom_serializer_and_engine_round_trip() -> None:
    index_cls = build_index(
        "builder_colors",
        id_type=UUID,
        model_type=Color,
        serializer=ColorSerializer,
        engine=MemoryEngine,
    )
    engine = MemoryEngine()
    index = index_cls(engine)

    index.set(USER_ID, Color("red"))
    assert isinstance(engine, Engine)
    assert engine.data[("builder_colors", str(USER_ID))] == "red"
    assert index.get(USER_ID) == Color("red")


def test_specialized_serializer_uses_its_model() -> None:
    index_cls = build_async_index(
        "builder_user_serializer",
        id_type=UUID,
        model_type=User,
        serializer=UserSerializer,
        engine=AsyncRedisHashEngine,
    )
    assert index_cls.model is User
    assert isinstance(index_cls.serializer, UserSerializer)

    with pytest.raises(TypeError):
        build_async_index(
            "builder_user_serializer_other",
            id_type=UUID,
            model_type=OtherUser,
            serializer=UserSerializer,
            engine=AsyncRedisHashEngine,
        )
    with pytest.raises(KeyError):
        get_async_index("builder_user_serializer_other")


def test_duplicate_key() -> None:
    first = build_index(
        "builder_duplicate",
        id_type=int,
        model_type=int,
        serializer=IntSerializer,
        engine=MemoryEngine,
    )
    with pytest.raises(ValueError):
        build_index(
            "builder_duplicate",
            id_type=int,
            model_type=int,
            serializer=IntSerializer,
            engine=MemoryEngine,
        )
    assert get_index("builder_duplicate") is first


def test_rejected_combinations_do_not_register() -> None:
    cases: tuple[tuple[str, bool, object], ...] = (
        (
            "builder_model_mismatch",
            False,
            lambda: build_index(
                "builder_model_mismatch",
                id_type=UUID,
                model_type=int,
                serializer=DatetimeSerializer,
                engine=RedisStringEngine,
            ),
        ),
        (
            "builder_bool",
            False,
            lambda: build_index(
                "builder_bool",
                id_type=int,
                model_type=bool,
                serializer=IntSerializer,
                engine=MemoryEngine,
            ),
        ),
        (
            "builder_bytes",
            False,
            lambda: build_index(
                "builder_bytes",
                id_type=int,
                model_type=int,
                serializer=IntSerializer,
                engine=BytesEngine,
            ),
        ),
        (
            "builder_uuid_field",
            False,
            lambda: build_index(
                "builder_uuid_field",
                id_type=UUID,
                model_type=datetime,
                serializer=DatetimeSerializer,
                engine=UuidFieldEngine,
            ),
        ),
        (
            "builder_sync_engine",
            True,
            lambda: build_async_index(
                "builder_sync_engine",
                id_type=int,
                model_type=int,
                serializer=IntSerializer,
                engine=MemoryEngine,
            ),
        ),
        (
            "builder_async_engine",
            False,
            lambda: build_index(
                "builder_async_engine",
                id_type=UUID,
                model_type=datetime,
                serializer=DatetimeSerializer,
                engine=AsyncRedisHashEngine,
            ),
        ),
        (
            "builder_pydantic_datetime",
            True,
            lambda: build_async_index(
                "builder_pydantic_datetime",
                id_type=UUID,
                model_type=datetime,
                serializer=PydanticSerializer,
                engine=AsyncRedisHashEngine,
            ),
        ),
        (
            "builder_plain_dict",
            False,
            lambda: build_index(
                "builder_plain_dict",
                id_type=int,
                model_type=dict,
                serializer=DictSerializer,
                engine=MemoryEngine,
            ),
        ),
        (
            "builder_needs_extra",
            False,
            lambda: build_index(
                "builder_needs_extra",
                id_type=int,
                model_type=int,
                serializer=NeedsExtra,
                engine=MemoryEngine,
            ),
        ),
        (
            "builder_not_dataclass",
            False,
            lambda: build_index(
                "builder_not_dataclass",
                id_type=int,
                model_type=int,
                serializer=DataclassSerializer,
                engine=MemoryEngine,
            ),
        ),
    )
    for key, async_index, build in cases:
        with pytest.raises(TypeError):
            build()
        getter = get_async_index if async_index else get_index
        with pytest.raises(KeyError):
            getter(key)


def test_empty_key() -> None:
    with pytest.raises(TypeError):
        build_index(
            "",
            id_type=int,
            model_type=int,
            serializer=IntSerializer,
            engine=MemoryEngine,
        )


def test_dict_alias_matches_dict_serializer() -> None:
    index_cls = build_index(
        "builder_dict_alias",
        id_type=int,
        model_type=dict[str, Any],
        serializer=DictSerializer,
        engine=MemoryEngine,
    )
    assert index_cls.model == dict[str, Any]
    assert isinstance(index_cls.serializer, DictSerializer)
