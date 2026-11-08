import asyncio
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, TypeVar
from uuid import UUID

import fakeredis
import pytest
from pydantic import BaseModel
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from cacher import (
    AsyncKeyValueIndex,
    DictSerializer,
    IntSerializer,
    KeyValueIndex,
    build_async_key_value_index,
    build_key_value_index,
    get_registry,
)
from cacher.indexes.base import _registries
from cacher.serializers.datetime_serializer import DatetimeSerializer
from cacher.serializers.pydantic_serializer import PydanticSerializer
from cacher.serializers.serializer import Serializer
from cacher.storage.key_value.async_redis_hash_storage import AsyncRedisHashStorage
from cacher.storage.key_value.redis_string_storage import RedisStringStorage
from cacher.storage.key_value.storage import KeyValueStorage

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


class Memory:
    pass


class MemoryStorage(KeyValueStorage[Memory, str, str]):
    def __init__(self) -> None:
        self.data: dict[tuple[str, str], str] = {}

    def get(self, client: Memory, name: str, field: str) -> str | None:
        return self.data.get((name, field))

    def set(
        self, client: Memory, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        self.data[(name, field)] = value

    def delete(self, client: Memory, name: str, field: str) -> None:
        self.data.pop((name, field), None)

    def exists(self, client: Memory, name: str, field: str) -> bool:
        return (name, field) in self.data

    def mget(self, client: Memory, name: str, fields: Sequence[str]) -> list[str | None]:
        return [self.data.get((name, field)) for field in fields]

    def mset(
        self, client: Memory, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        for field, value in items.items():
            self.data[(name, field)] = value


class BytesStorage(KeyValueStorage[Memory, str, bytes]):
    pass


class UuidFieldStorage(KeyValueStorage[Memory, UUID, str]):
    pass


def test_builders_are_public() -> None:
    import cacher

    assert cacher.build_key_value_index is build_key_value_index
    assert cacher.build_async_key_value_index is build_async_key_value_index


def test_sync_datetime_index_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisStringStorage()
    index = build_key_value_index(
        "user_last_activities",
        id_type=UUID,
        model_type=datetime,
        serializer=DatetimeSerializer(),
        storage=storage,
    )

    assert index is get_registry(Redis).get("user_last_activities")
    assert index.client_type is Redis
    assert isinstance(index, KeyValueIndex)
    assert index.identifier is UUID
    assert index.model is datetime
    assert index.key == "user_last_activities"
    assert index.storage is storage
    assert isinstance(index.serializer, DatetimeSerializer)

    assert index.get(client, USER_ID) is None
    index.set(client, USER_ID, MOMENT)
    assert client.get(f"user_last_activities:{USER_ID}") == MOMENT.isoformat()
    assert index.get(client, USER_ID) == MOMENT


def test_async_pydantic_index_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        try:
            storage = AsyncRedisHashStorage()
            index = build_async_key_value_index(
                "builder_users",
                id_type=UUID,
                model_type=User,
                serializer=PydanticSerializer(User),
                storage=storage,
            )
            assert index is get_registry(AsyncRedis).get("builder_users")
            assert index.client_type is AsyncRedis
            assert isinstance(index, AsyncKeyValueIndex)
            assert index.identifier is UUID
            assert index.model is User
            assert index.storage is storage
            assert isinstance(index.serializer, PydanticSerializer)

            user = User(id=1, name="Ada")
            await index.set(client, USER_ID, user)
            stored = await client.hget("builder_users", str(USER_ID))
            assert stored == user.model_dump_json()
            assert await index.get(client, USER_ID) == user
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_serializer_subclass_keeps_parent_types() -> None:
    index = build_key_value_index(
        "builder_activity_subclass",
        id_type=UUID,
        model_type=datetime,
        serializer=ActivitySerializer(),
        storage=RedisStringStorage(),
    )
    assert isinstance(index.serializer, ActivitySerializer)
    assert index.model is datetime


def test_custom_serializer_and_storage_round_trip() -> None:
    storage = MemoryStorage()
    index = build_key_value_index(
        "builder_colors",
        id_type=UUID,
        model_type=Color,
        serializer=ColorSerializer(),
        storage=storage,
    )
    client = Memory()

    index.set(client, USER_ID, Color("red"))
    assert isinstance(storage, KeyValueStorage)
    assert storage.data[("builder_colors", str(USER_ID))] == "red"
    assert index.get(client, USER_ID) == Color("red")


def test_specialized_serializer_uses_its_model() -> None:
    index = build_async_key_value_index(
        "builder_user_serializer",
        id_type=UUID,
        model_type=User,
        serializer=UserSerializer(User),
        storage=AsyncRedisHashStorage(),
    )
    assert index.model is User
    assert isinstance(index.serializer, UserSerializer)

    with pytest.raises(TypeError):
        build_async_key_value_index(
            "builder_user_serializer_other",
            id_type=UUID,
            model_type=OtherUser,
            serializer=UserSerializer(User),
            storage=AsyncRedisHashStorage(),
        )
    with pytest.raises(KeyError):
        get_registry(AsyncRedis).get("builder_user_serializer_other")


def test_duplicate_key() -> None:
    first = build_key_value_index(
        "builder_duplicate",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=MemoryStorage(),
    )
    with pytest.raises(ValueError):
        build_key_value_index(
            "builder_duplicate",
            id_type=int,
            model_type=int,
            serializer=IntSerializer(),
            storage=MemoryStorage(),
        )
    assert get_registry(Memory).get("builder_duplicate") is first


def test_rejected_combinations_do_not_register() -> None:
    cases: tuple[tuple[str, object], ...] = (
        (
            "builder_model_mismatch",
            lambda: build_key_value_index(
                "builder_model_mismatch",
                id_type=UUID,
                model_type=int,
                serializer=DatetimeSerializer(),
                storage=RedisStringStorage(),
            ),
        ),
        (
            "builder_bool",
            lambda: build_key_value_index(
                "builder_bool",
                id_type=int,
                model_type=bool,
                serializer=IntSerializer(),
                storage=MemoryStorage(),
            ),
        ),
        (
            "builder_bytes",
            lambda: build_key_value_index(
                "builder_bytes",
                id_type=int,
                model_type=int,
                serializer=IntSerializer(),
                storage=BytesStorage(),
            ),
        ),
        (
            "builder_uuid_field",
            lambda: build_key_value_index(
                "builder_uuid_field",
                id_type=UUID,
                model_type=datetime,
                serializer=DatetimeSerializer(),
                storage=UuidFieldStorage(),
            ),
        ),
        (
            "builder_sync_storage",
            lambda: build_async_key_value_index(
                "builder_sync_storage",
                id_type=int,
                model_type=int,
                serializer=IntSerializer(),
                storage=MemoryStorage(),
            ),
        ),
        (
            "builder_async_storage",
            lambda: build_key_value_index(
                "builder_async_storage",
                id_type=UUID,
                model_type=datetime,
                serializer=DatetimeSerializer(),
                storage=AsyncRedisHashStorage(),
            ),
        ),
        (
            "builder_pydantic_datetime",
            lambda: build_async_key_value_index(
                "builder_pydantic_datetime",
                id_type=UUID,
                model_type=datetime,
                serializer=PydanticSerializer(User),
                storage=AsyncRedisHashStorage(),
            ),
        ),
        (
            "builder_plain_dict",
            lambda: build_key_value_index(
                "builder_plain_dict",
                id_type=int,
                model_type=dict,
                serializer=DictSerializer(),
                storage=MemoryStorage(),
            ),
        ),
    )
    for key, build in cases:
        with pytest.raises(TypeError):
            build()
        assert_unregistered(key)


def assert_unregistered(key: str) -> None:
    for client in (Memory, Redis, AsyncRedis):
        try:
            registry = get_registry(client)
        except KeyError:
            continue
        assert key not in registry


_UnspecifiedClient = TypeVar("_UnspecifiedClient")


class NoClientStorage(KeyValueStorage[_UnspecifiedClient, str, str]):
    pass


def test_class_arguments_do_not_register() -> None:
    with pytest.raises(TypeError):
        build_key_value_index(
            "builder_serializer_class",
            id_type=int,
            model_type=int,
            serializer=IntSerializer,
            storage=MemoryStorage(),
        )
    assert_unregistered("builder_serializer_class")
    with pytest.raises(TypeError):
        build_key_value_index(
            "builder_storage_class",
            id_type=int,
            model_type=int,
            serializer=IntSerializer(),
            storage=RedisStringStorage,
        )
    assert_unregistered("builder_storage_class")


def test_different_clients_can_share_an_index_key() -> None:
    memory = build_key_value_index(
        "client_shared_key",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=MemoryStorage(),
    )
    redis = build_key_value_index(
        "client_shared_key",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=RedisStringStorage(),
    )
    assert get_registry(Memory).get("client_shared_key") is memory
    assert get_registry(Redis).get("client_shared_key") is redis
    assert memory is not redis


def test_missing_client_type_does_not_register() -> None:
    before = {client: set(registry) for client, registry in _registries.items()}
    with pytest.raises(TypeError):
        build_key_value_index(
            "builder_no_client",
            id_type=int,
            model_type=int,
            serializer=IntSerializer(),
            storage=NoClientStorage(),
        )
    after = {client: set(registry) for client, registry in _registries.items()}
    assert after == before


def test_empty_key() -> None:
    with pytest.raises(TypeError):
        build_key_value_index(
            "",
            id_type=int,
            model_type=int,
            serializer=IntSerializer(),
            storage=MemoryStorage(),
        )


def test_dict_alias_matches_dict_serializer() -> None:
    index = build_key_value_index(
        "builder_dict_alias",
        id_type=int,
        model_type=dict[str, Any],
        serializer=DictSerializer(),
        storage=MemoryStorage(),
    )
    assert index.model == dict[str, Any]
    assert isinstance(index.serializer, DictSerializer)
