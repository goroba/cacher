import asyncio
from collections.abc import Sequence

import fakeredis

from cacher.storage import AsyncRedisStringStorage, RedisStringStorage
from cacher.storage.key_value.async_storage import AsyncKeyValueStorage
from cacher.storage.key_value.storage import KeyValueStorage

_NAME = "users"


class _MgetSpy:
    def __init__(self) -> None:
        self.called = False

    def mget(self, keys: Sequence[str]) -> list[str | None]:
        self.called = True
        return [None for _ in keys]

    def mset(self, items: dict[str, str]) -> None:
        self.called = True


def test_sync_storage_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    storage = RedisStringStorage(client)

    assert isinstance(storage, KeyValueStorage)
    assert storage.get(_NAME, "missing") is None
    assert storage.exists(_NAME, "missing") is False
    storage.delete(_NAME, "missing")

    storage.set(_NAME, "a", "1", ttl=10)
    assert storage.get(_NAME, "a") == "1"
    assert storage.exists(_NAME, "a") is True
    assert client.get("users:a") == "1"
    assert 0 < client.ttl("users:a") <= 10

    storage.mset(_NAME, {"b": "2", "c": "3"})
    assert client.ttl("users:b") == -1
    assert storage.mget(_NAME, ["b", "a", "b", "missing"]) == ["2", "1", "2", None]

    storage.mset(_NAME, {"b": "20", "c": "30"}, ttl=5)
    assert storage.get(_NAME, "b") == "20"
    assert client.get("users:b") == "20"
    assert client.get("users:c") == "30"
    assert 0 < client.ttl("users:b") <= 5
    assert 0 < client.ttl("users:c") <= 5

    storage.delete(_NAME, "a")
    assert storage.get(_NAME, "a") is None
    assert storage.exists(_NAME, "a") is False


def test_sync_storage_empty_batches_do_not_call_redis() -> None:
    spy = _MgetSpy()
    storage = RedisStringStorage(spy)  # type: ignore[arg-type]

    assert storage.mget(_NAME, []) == []
    storage.mset(_NAME, {})
    assert spy.called is False


def test_sync_storage_decodes_bytes() -> None:
    client = fakeredis.FakeRedis(decode_responses=False)
    storage = RedisStringStorage(client)

    storage.set(_NAME, "a", "hello")
    assert client.get("users:a") == b"hello"
    assert storage.get(_NAME, "a") == "hello"
    assert storage.mget(_NAME, ["a", "missing"]) == ["hello", None]


def test_async_storage_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisStringStorage(client)
        try:
            assert isinstance(storage, AsyncKeyValueStorage)
            assert await storage.get(_NAME, "missing") is None
            assert await storage.exists(_NAME, "missing") is False
            await storage.delete(_NAME, "missing")

            await storage.set(_NAME, "a", "1", ttl=10)
            assert await storage.get(_NAME, "a") == "1"
            assert await storage.exists(_NAME, "a") is True
            assert await client.get("users:a") == "1"
            assert 0 < await client.ttl("users:a") <= 10

            await storage.mset(_NAME, {"b": "2", "c": "3"})
            assert await client.ttl("users:b") == -1
            assert await storage.mget(_NAME, ["b", "a", "b", "missing"]) == ["2", "1", "2", None]

            await storage.mset(_NAME, {"b": "20", "c": "30"}, ttl=5)
            assert await storage.get(_NAME, "b") == "20"
            assert await client.get("users:b") == "20"
            assert await client.get("users:c") == "30"
            assert 0 < await client.ttl("users:b") <= 5
            assert 0 < await client.ttl("users:c") <= 5

            await storage.delete(_NAME, "a")
            assert await storage.get(_NAME, "a") is None
            assert await storage.exists(_NAME, "a") is False
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_async_storage_empty_batches_do_not_call_redis() -> None:
    spy = _MgetSpy()
    storage = AsyncRedisStringStorage(spy)  # type: ignore[arg-type]

    async def scenario() -> None:
        assert await storage.mget(_NAME, []) == []
        await storage.mset(_NAME, {})

    asyncio.run(scenario())
    assert spy.called is False


def test_async_storage_decodes_bytes() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=False)
        storage = AsyncRedisStringStorage(client)
        try:
            await storage.set(_NAME, "a", "hello")
            assert await client.get("users:a") == b"hello"
            assert await storage.get(_NAME, "a") == "hello"
            assert await storage.mget(_NAME, ["a", "missing"]) == ["hello", None]
        finally:
            await client.aclose()

    asyncio.run(scenario())
