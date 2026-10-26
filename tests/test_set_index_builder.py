import asyncio
from collections.abc import Sequence

import fakeredis
import pytest

from cacher import (
    AsyncSetIndex,
    IntSerializer,
    SetIndex,
    build_async_set_index,
    build_key_value_index,
    build_set_index,
    get_async_set_index,
    get_key_value_index,
    get_set_index,
)
from cacher.engines.key_value.redis_string_engine import RedisStringEngine
from cacher.engines.sets.async_engine import AsyncSetEngine
from cacher.engines.sets.async_redis_set_engine import AsyncRedisSetEngine
from cacher.engines.sets.engine import SetEngine
from cacher.engines.sets.redis_set_engine import RedisSetEngine
from cacher.serializers.datetime_serializer import DatetimeSerializer


class SpySet(SetEngine[str]):
    def __init__(self) -> None:
        self.called = False

    def madd(self, name: str, members: Sequence[str]) -> None:
        self.called = True

    def mremove(self, name: str, members: Sequence[str]) -> None:
        self.called = True


class AsyncSpySet(AsyncSetEngine[str]):
    def __init__(self) -> None:
        self.called = False

    async def madd(self, name: str, members: Sequence[str]) -> None:
        self.called = True

    async def mremove(self, name: str, members: Sequence[str]) -> None:
        self.called = True


class BytesSet(SetEngine[bytes]):
    pass


def test_set_builders_are_public() -> None:
    import cacher

    assert cacher.build_set_index is build_set_index
    assert cacher.build_async_set_index is build_async_set_index


def test_sync_set_index_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    index_cls = build_set_index(
        "active_users",
        member_type=int,
        serializer=IntSerializer,
        engine=RedisSetEngine,
    )
    assert index_cls is get_set_index("active_users")
    assert issubclass(index_cls, SetIndex)
    assert index_cls.member is int
    assert index_cls.key == "active_users"
    assert index_cls.engine is RedisSetEngine
    assert isinstance(index_cls.serializer, IntSerializer)

    engine = RedisSetEngine(client)
    index = index_cls(engine)
    assert isinstance(index, SetIndex)
    assert index.engine is engine

    assert index.contains(1) is False
    index.remove(1)
    index.add(1)
    index.add(1)
    assert index.contains(1) is True
    assert client.sismember("active_users", "1") == 1

    index.madd([3, 2])
    assert index.contains(2) is True
    assert index.contains(3) is True
    assert client.smembers("active_users") == {"1", "2", "3"}

    index.mremove([1, 3])
    assert index.contains(1) is False
    assert index.contains(3) is False
    assert index.contains(2) is True
    index.remove(2)
    assert index.contains(2) is False


def test_async_set_index_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        index_cls = build_async_set_index(
            "async_active_users",
            member_type=int,
            serializer=IntSerializer,
            engine=AsyncRedisSetEngine,
        )
        assert index_cls is get_async_set_index("async_active_users")
        assert issubclass(index_cls, AsyncSetIndex)
        assert index_cls.member is int
        assert index_cls.engine is AsyncRedisSetEngine

        engine = AsyncRedisSetEngine(client)
        index = index_cls(engine)
        try:
            assert isinstance(index, AsyncSetIndex)
            assert await index.contains(1) is False
            await index.remove(1)
            await index.add(1)
            await index.add(1)
            assert await index.contains(1) is True
            assert await client.sismember("async_active_users", "1") == 1

            await index.madd([3, 2])
            assert await index.contains(2) is True
            assert await index.contains(3) is True
            assert await client.smembers("async_active_users") == {"1", "2", "3"}

            await index.mremove([1, 3])
            assert await index.contains(1) is False
            assert await index.contains(2) is True
            await index.remove(2)
            assert await index.contains(2) is False
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_duplicate_set_key() -> None:
    first = build_set_index(
        "set_duplicate",
        member_type=int,
        serializer=IntSerializer,
        engine=RedisSetEngine,
    )
    with pytest.raises(ValueError):
        build_set_index(
            "set_duplicate",
            member_type=int,
            serializer=IntSerializer,
            engine=RedisSetEngine,
        )
    assert get_set_index("set_duplicate") is first


def test_key_value_and_set_indexes_share_a_key() -> None:
    key_value = build_key_value_index(
        "shared_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer,
        engine=RedisStringEngine,
    )
    members = build_set_index(
        "shared_users",
        member_type=int,
        serializer=IntSerializer,
        engine=RedisSetEngine,
    )
    assert get_key_value_index("shared_users") is key_value
    assert get_set_index("shared_users") is members


def test_rejected_set_indexes_do_not_register() -> None:
    cases: tuple[tuple[str, bool, object], ...] = (
        (
            "set_member_mismatch",
            False,
            lambda: build_set_index(
                "set_member_mismatch",
                member_type=int,
                serializer=DatetimeSerializer,
                engine=RedisSetEngine,
            ),
        ),
        (
            "set_storage_mismatch",
            False,
            lambda: build_set_index(
                "set_storage_mismatch",
                member_type=int,
                serializer=IntSerializer,
                engine=BytesSet,
            ),
        ),
        (
            "set_sync_engine",
            True,
            lambda: build_async_set_index(
                "set_sync_engine",
                member_type=int,
                serializer=IntSerializer,
                engine=SpySet,
            ),
        ),
    )
    for key, async_index, build in cases:
        with pytest.raises(TypeError):
            build()
        getter = get_async_set_index if async_index else get_set_index
        with pytest.raises(KeyError):
            getter(key)


def test_empty_set_batches_do_not_call_engine() -> None:
    index_cls = build_set_index(
        "set_empty_batches",
        member_type=int,
        serializer=IntSerializer,
        engine=SpySet,
    )
    engine = SpySet()
    index = index_cls(engine)
    index.madd([])
    index.mremove([])
    assert engine.called is False


def test_async_empty_set_batches_do_not_call_engine() -> None:
    index_cls = build_async_set_index(
        "async_set_empty_batches",
        member_type=int,
        serializer=IntSerializer,
        engine=AsyncSpySet,
    )
    engine = AsyncSpySet()
    index = index_cls(engine)

    async def scenario() -> None:
        await index.madd([])
        await index.mremove([])

    asyncio.run(scenario())
    assert engine.called is False
