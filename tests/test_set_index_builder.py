import asyncio
from collections.abc import Sequence

import fakeredis
import pytest

from cacher import (
    AsyncSetIndex,
    IntSerializer,
    SetIndex,
    build_async_key_value_index,
    build_async_set_index,
    build_key_value_index,
    build_set_index,
    get_async_index,
    get_index,
)
from cacher.serializers.datetime_serializer import DatetimeSerializer
from cacher.storage.key_value.async_redis_string_storage import AsyncRedisStringStorage
from cacher.storage.key_value.redis_string_storage import RedisStringStorage
from cacher.storage.sets.async_redis_set_storage import AsyncRedisSetStorage
from cacher.storage.sets.async_storage import AsyncSetStorage
from cacher.storage.sets.redis_set_storage import RedisSetStorage
from cacher.storage.sets.storage import SetStorage


class SpySet(SetStorage[str]):
    def __init__(self) -> None:
        self.called = False

    def madd(self, name: str, members: Sequence[str]) -> None:
        self.called = True

    def mremove(self, name: str, members: Sequence[str]) -> None:
        self.called = True


class AsyncSpySet(AsyncSetStorage[str]):
    def __init__(self) -> None:
        self.called = False

    async def madd(self, name: str, members: Sequence[str]) -> None:
        self.called = True

    async def mremove(self, name: str, members: Sequence[str]) -> None:
        self.called = True


class BytesSet(SetStorage[bytes]):
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
        storage=RedisSetStorage,
    )
    assert index_cls is get_index("active_users")
    assert issubclass(index_cls, SetIndex)
    assert index_cls.member is int
    assert index_cls.key == "active_users"
    assert index_cls.storage is RedisSetStorage
    assert isinstance(index_cls.serializer, IntSerializer)

    storage = RedisSetStorage(client)
    index = index_cls(storage)
    assert isinstance(index, SetIndex)
    assert index.storage is storage

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
            storage=AsyncRedisSetStorage,
        )
        assert index_cls is get_async_index("async_active_users")
        assert issubclass(index_cls, AsyncSetIndex)
        assert index_cls.member is int
        assert index_cls.storage is AsyncRedisSetStorage

        storage = AsyncRedisSetStorage(client)
        index = index_cls(storage)
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
        storage=RedisSetStorage,
    )
    with pytest.raises(ValueError):
        build_set_index(
            "set_duplicate",
            member_type=int,
            serializer=IntSerializer,
            storage=RedisSetStorage,
        )
    assert get_index("set_duplicate") is first


def test_sync_and_async_set_indexes_use_separate_registries() -> None:
    sync = build_set_index(
        "set_sync_async",
        member_type=int,
        serializer=IntSerializer,
        storage=RedisSetStorage,
    )
    async_index = build_async_set_index(
        "set_sync_async",
        member_type=int,
        serializer=IntSerializer,
        storage=AsyncRedisSetStorage,
    )
    assert get_index("set_sync_async") is sync
    assert get_async_index("set_sync_async") is async_index


def test_sync_key_value_and_set_indexes_share_a_registry() -> None:
    key_value = build_key_value_index(
        "shared_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer,
        storage=RedisStringStorage,
    )
    with pytest.raises(ValueError):
        build_set_index(
            "shared_users",
            member_type=int,
            serializer=IntSerializer,
            storage=RedisSetStorage,
        )
    assert get_index("shared_users") is key_value


def test_async_key_value_and_set_indexes_share_a_registry() -> None:
    key_value = build_async_key_value_index(
        "async_shared_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer,
        storage=AsyncRedisStringStorage,
    )
    with pytest.raises(ValueError):
        build_async_set_index(
            "async_shared_users",
            member_type=int,
            serializer=IntSerializer,
            storage=AsyncRedisSetStorage,
        )
    assert get_async_index("async_shared_users") is key_value


def test_rejected_set_indexes_do_not_register() -> None:
    cases: tuple[tuple[str, bool, object], ...] = (
        (
            "set_member_mismatch",
            False,
            lambda: build_set_index(
                "set_member_mismatch",
                member_type=int,
                serializer=DatetimeSerializer,
                storage=RedisSetStorage,
            ),
        ),
        (
            "set_storage_mismatch",
            False,
            lambda: build_set_index(
                "set_storage_mismatch",
                member_type=int,
                serializer=IntSerializer,
                storage=BytesSet,
            ),
        ),
        (
            "set_sync_storage",
            True,
            lambda: build_async_set_index(
                "set_sync_storage",
                member_type=int,
                serializer=IntSerializer,
                storage=SpySet,
            ),
        ),
    )
    for key, async_index, build in cases:
        with pytest.raises(TypeError):
            build()
        getter = get_async_index if async_index else get_index
        with pytest.raises(KeyError):
            getter(key)


def test_empty_set_batches_do_not_call_storage() -> None:
    index_cls = build_set_index(
        "set_empty_batches",
        member_type=int,
        serializer=IntSerializer,
        storage=SpySet,
    )
    storage = SpySet()
    index = index_cls(storage)
    index.madd([])
    index.mremove([])
    assert storage.called is False


def test_async_empty_set_batches_do_not_call_storage() -> None:
    index_cls = build_async_set_index(
        "async_set_empty_batches",
        member_type=int,
        serializer=IntSerializer,
        storage=AsyncSpySet,
    )
    storage = AsyncSpySet()
    index = index_cls(storage)

    async def scenario() -> None:
        await index.madd([])
        await index.mremove([])

    asyncio.run(scenario())
    assert storage.called is False
