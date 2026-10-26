import asyncio
from collections.abc import Sequence

import fakeredis

from cacher.storage.key_value.async_redis_hash_storage import AsyncRedisHashStorage
from cacher.storage.key_value.async_storage import AsyncKeyValueStorage
from cacher.storage.key_value.redis_hash_storage import RedisHashStorage
from cacher.storage.key_value.storage import KeyValueStorage


class _HashSpy:
    def __init__(self) -> None:
        self.hmget_called = False
        self.hset_called = False

    def hmget(self, name: str, keys: Sequence[str]) -> list[str | None]:
        self.hmget_called = True
        return [None for _ in keys]

    def hset(
        self,
        name: str,
        key: str | None = None,
        value: str | None = None,
        mapping: dict[str, str] | None = None,
    ) -> int:
        self.hset_called = True
        return 0


def test_sync_hash_storage_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisHashStorage(client)
    assert isinstance(storage, KeyValueStorage)

    assert storage.get("users", "1") is None
    assert storage.exists("users", "1") is False
    storage.delete("users", "1")

    storage.set("users", "1", "10", ttl=30)
    assert storage.get("users", "1") == "10"
    assert storage.exists("users", "1") is True
    assert 0 < client.httl("users", "1")[0] <= 30

    storage.mset("users", {"2": "20", "3": "30"})
    assert storage.mget("users", ["2", "1", "2", "9"]) == ["20", "10", "20", None]
    assert client.httl("users", "2")[0] == -1

    storage.mset("users", {"2": "21", "4": "40"}, ttl=5)
    assert storage.get("users", "2") == "21"
    assert 0 < client.httl("users", "2")[0] <= 5
    assert 0 < client.httl("users", "4")[0] <= 5
    assert client.httl("users", "1")[0] > 5

    storage.delete("users", "1")
    assert storage.get("users", "1") is None
    assert storage.exists("users", "1") is False


def test_sync_hash_storage_empty_batches_do_not_call_redis() -> None:
    spy = _HashSpy()
    storage = RedisHashStorage(spy)  # type: ignore[arg-type]

    assert storage.mget("users", []) == []
    storage.mset("users", {})
    assert spy.hmget_called is False
    assert spy.hset_called is False


def test_sync_hash_storage_decodes_bytes() -> None:
    client = fakeredis.FakeRedis(decode_responses=False)
    storage = RedisHashStorage(client)

    storage.set("users", "1", "10")
    assert client.hget("users", "1") == b"10"
    assert storage.get("users", "1") == "10"
    assert storage.mget("users", ["1", "2"]) == ["10", None]


def test_async_hash_storage_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisHashStorage(client)
        assert isinstance(storage, AsyncKeyValueStorage)
        try:
            assert await storage.get("users", "1") is None
            assert await storage.exists("users", "1") is False
            await storage.delete("users", "1")

            await storage.set("users", "1", "10", ttl=30)
            assert await storage.get("users", "1") == "10"
            assert await storage.exists("users", "1") is True
            assert 0 < (await client.httl("users", "1"))[0] <= 30

            await storage.mset("users", {"2": "20", "3": "30"})
            assert await storage.mget("users", ["2", "1", "2", "9"]) == ["20", "10", "20", None]
            assert (await client.httl("users", "2"))[0] == -1

            await storage.mset("users", {"2": "21", "4": "40"}, ttl=5)
            assert await storage.get("users", "2") == "21"
            assert 0 < (await client.httl("users", "2"))[0] <= 5
            assert 0 < (await client.httl("users", "4"))[0] <= 5
            assert (await client.httl("users", "1"))[0] > 5

            await storage.delete("users", "1")
            assert await storage.get("users", "1") is None
            assert await storage.exists("users", "1") is False
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_async_hash_storage_empty_batches_do_not_call_redis() -> None:
    spy = _HashSpy()
    storage = AsyncRedisHashStorage(spy)  # type: ignore[arg-type]

    async def scenario() -> None:
        assert await storage.mget("users", []) == []
        await storage.mset("users", {})

    asyncio.run(scenario())
    assert spy.hmget_called is False
    assert spy.hset_called is False


def test_async_hash_storage_decodes_bytes() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=False)
        storage = AsyncRedisHashStorage(client)
        try:
            await storage.set("users", "1", "10")
            assert await client.hget("users", "1") == b"10"
            assert await storage.get("users", "1") == "10"
            assert await storage.mget("users", ["1", "2"]) == ["10", None]
        finally:
            await client.aclose()

    asyncio.run(scenario())
