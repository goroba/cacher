import asyncio
from collections.abc import Sequence

import fakeredis

from cacher.storage import AsyncRedisSetStorage, RedisSetStorage
from cacher.storage.sets.async_storage import AsyncSetStorage
from cacher.storage.sets.storage import SetStorage


class _SetSpy:
    def __init__(self) -> None:
        self.called = False

    def sadd(self, name: str, *members: str) -> int:
        self.called = True
        return 0

    def srem(self, name: str, *members: str) -> int:
        self.called = True
        return 0


def test_sync_set_storage_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisSetStorage(client)
    assert isinstance(storage, SetStorage)

    assert storage.contains("users", "1") is False
    storage.remove("users", "1")
    assert storage.contains("users", "1") is False

    storage.add("users", "1")
    storage.add("users", "1")
    assert storage.contains("users", "1") is True
    assert client.sismember("users", "1") == 1

    storage.madd("users", ["3", "2"])
    assert storage.contains("users", "2") is True
    assert storage.contains("users", "3") is True
    assert client.smembers("users") == {"1", "2", "3"}

    storage.mremove("users", ["1", "3"])
    assert storage.contains("users", "1") is False
    assert storage.contains("users", "3") is False
    assert storage.contains("users", "2") is True
    storage.remove("users", "2")
    assert storage.contains("users", "2") is False


def test_sync_set_storage_empty_batches_do_not_call_redis() -> None:
    spy = _SetSpy()
    storage = RedisSetStorage(spy)  # type: ignore[arg-type]

    storage.madd("users", [])
    storage.mremove("users", [])
    assert spy.called is False


def test_async_set_storage_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisSetStorage(client)
        assert isinstance(storage, AsyncSetStorage)
        try:
            assert await storage.contains("users", "1") is False
            await storage.remove("users", "1")
            assert await storage.contains("users", "1") is False

            await storage.add("users", "1")
            await storage.add("users", "1")
            assert await storage.contains("users", "1") is True
            assert await client.sismember("users", "1") == 1

            await storage.madd("users", ["3", "2"])
            assert await storage.contains("users", "2") is True
            assert await storage.contains("users", "3") is True
            assert await client.smembers("users") == {"1", "2", "3"}

            await storage.mremove("users", ["1", "3"])
            assert await storage.contains("users", "1") is False
            assert await storage.contains("users", "3") is False
            assert await storage.contains("users", "2") is True
            await storage.remove("users", "2")
            assert await storage.contains("users", "2") is False
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_async_set_storage_empty_batches_do_not_call_redis() -> None:
    spy = _SetSpy()
    storage = AsyncRedisSetStorage(spy)  # type: ignore[arg-type]

    async def scenario() -> None:
        await storage.madd("users", [])
        await storage.mremove("users", [])

    asyncio.run(scenario())
    assert spy.called is False
