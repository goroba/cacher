import asyncio
from collections.abc import Sequence

import fakeredis
import pytest
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from cacher import (
    AsyncSetIndex,
    IntSerializer,
    SetIndex,
    build_async_key_value_index,
    build_async_set_index,
    build_key_value_index,
    build_set_index,
    get_registry,
)
from cacher.serializers.datetime_serializer import DatetimeSerializer
from cacher.storage.key_value.async_redis_string_storage import AsyncRedisStringStorage
from cacher.storage.key_value.redis_string_storage import RedisStringStorage
from cacher.storage.sets.async_redis_set_storage import AsyncRedisSetStorage
from cacher.storage.sets.async_storage import AsyncSetStorage
from cacher.storage.sets.redis_set_storage import RedisSetStorage
from cacher.storage.sets.storage import SetStorage


class Spy:
    pass


class SpySet(SetStorage[Spy, str]):
    def __init__(self) -> None:
        self.called = False

    def madd(self, client: Spy, name: str, members: Sequence[str]) -> None:
        self.called = True

    def mremove(self, client: Spy, name: str, members: Sequence[str]) -> None:
        self.called = True


class AsyncSpy:
    pass


class AsyncSpySet(AsyncSetStorage[AsyncSpy, str]):
    def __init__(self) -> None:
        self.called = False

    async def madd(self, client: AsyncSpy, name: str, members: Sequence[str]) -> None:
        self.called = True

    async def mremove(self, client: AsyncSpy, name: str, members: Sequence[str]) -> None:
        self.called = True


class BytesSet(SetStorage[Spy, bytes]):
    pass


def test_set_builders_are_public() -> None:
    import cacher

    assert cacher.build_set_index is build_set_index
    assert cacher.build_async_set_index is build_async_set_index


def test_sync_set_index_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisSetStorage()
    index = build_set_index(
        "active_users",
        member_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    assert index is get_registry(Redis).get("active_users")
    assert index.client_type is Redis
    assert isinstance(index, SetIndex)
    assert index.member is int
    assert index.key == "active_users"
    assert index.storage is storage
    assert isinstance(index.serializer, IntSerializer)

    assert index.contains(client, 1) is False
    index.remove(client, 1)
    index.add(client, 1)
    index.add(client, 1)
    assert index.contains(client, 1) is True
    assert client.sismember("active_users", "1") == 1

    index.madd(client, [3, 2])
    assert index.contains(client, 2) is True
    assert index.contains(client, 3) is True
    assert client.smembers("active_users") == {"1", "2", "3"}

    index.mremove(client, [1, 3])
    assert index.contains(client, 1) is False
    assert index.contains(client, 3) is False
    assert index.contains(client, 2) is True
    index.remove(client, 2)
    assert index.contains(client, 2) is False


def test_async_set_index_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        try:
            storage = AsyncRedisSetStorage()
            index = build_async_set_index(
                "async_active_users",
                member_type=int,
                serializer=IntSerializer(),
                storage=storage,
            )
            assert index is get_registry(AsyncRedis).get("async_active_users")
            assert index.client_type is AsyncRedis
            assert isinstance(index, AsyncSetIndex)
            assert index.member is int
            assert index.storage is storage

            assert await index.contains(client, 1) is False
            await index.remove(client, 1)
            await index.add(client, 1)
            await index.add(client, 1)
            assert await index.contains(client, 1) is True
            assert await client.sismember("async_active_users", "1") == 1

            await index.madd(client, [3, 2])
            assert await index.contains(client, 2) is True
            assert await index.contains(client, 3) is True
            assert await client.smembers("async_active_users") == {"1", "2", "3"}

            await index.mremove(client, [1, 3])
            assert await index.contains(client, 1) is False
            assert await index.contains(client, 2) is True
            await index.remove(client, 2)
            assert await index.contains(client, 2) is False
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_duplicate_set_key() -> None:
    first = build_set_index(
        "set_duplicate",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisSetStorage(),
    )
    with pytest.raises(ValueError):
        build_set_index(
            "set_duplicate",
            member_type=int,
            serializer=IntSerializer(),
            storage=RedisSetStorage(),
        )
    assert get_registry(Redis).get("set_duplicate") is first


def test_redis_and_async_redis_can_share_an_index_key() -> None:
    sync = build_set_index(
        "set_sync_async",
        member_type=int,
        serializer=IntSerializer(),
        storage=RedisSetStorage(),
    )
    async_index = build_async_set_index(
        "set_sync_async",
        member_type=int,
        serializer=IntSerializer(),
        storage=AsyncRedisSetStorage(),
    )
    assert get_registry(Redis).get("set_sync_async") is sync
    assert get_registry(AsyncRedis).get("set_sync_async") is async_index


def test_same_client_key_value_and_set_indexes_share_a_registry() -> None:
    key_value = build_key_value_index(
        "shared_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=RedisStringStorage(),
    )
    with pytest.raises(ValueError):
        build_set_index(
            "shared_users",
            member_type=int,
            serializer=IntSerializer(),
            storage=RedisSetStorage(),
        )
    assert get_registry(Redis).get("shared_users") is key_value


def test_same_async_client_key_value_and_set_indexes_share_a_registry() -> None:
    key_value = build_async_key_value_index(
        "async_shared_users",
        id_type=int,
        model_type=int,
        serializer=IntSerializer(),
        storage=AsyncRedisStringStorage(),
    )
    with pytest.raises(ValueError):
        build_async_set_index(
            "async_shared_users",
            member_type=int,
            serializer=IntSerializer(),
            storage=AsyncRedisSetStorage(),
        )
    assert get_registry(AsyncRedis).get("async_shared_users") is key_value


def test_rejected_set_indexes_do_not_register() -> None:
    cases: tuple[tuple[str, object], ...] = (
        (
            "set_member_mismatch",
            lambda: build_set_index(
                "set_member_mismatch",
                member_type=int,
                serializer=DatetimeSerializer(),
                storage=RedisSetStorage(),
            ),
        ),
        (
            "set_storage_mismatch",
            lambda: build_set_index(
                "set_storage_mismatch",
                member_type=int,
                serializer=IntSerializer(),
                storage=BytesSet(),
            ),
        ),
        (
            "set_sync_storage",
            lambda: build_async_set_index(
                "set_sync_storage",
                member_type=int,
                serializer=IntSerializer(),
                storage=SpySet(),
            ),
        ),
    )
    for key, build in cases:
        with pytest.raises(TypeError):
            build()
        for client in (Redis, AsyncRedis, Spy):
            try:
                registry = get_registry(client)
            except KeyError:
                continue
            assert key not in registry


def test_empty_set_batches_do_not_call_storage() -> None:
    storage = SpySet()
    index = build_set_index(
        "set_empty_batches",
        member_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    client = Spy()
    index.madd(client, [])
    index.mremove(client, [])
    assert storage.called is False


def test_async_empty_set_batches_do_not_call_storage() -> None:
    storage = AsyncSpySet()
    index = build_async_set_index(
        "async_set_empty_batches",
        member_type=int,
        serializer=IntSerializer(),
        storage=storage,
    )
    client = AsyncSpy()

    async def scenario() -> None:
        await index.madd(client, [])
        await index.mremove(client, [])

    asyncio.run(scenario())
    assert storage.called is False
