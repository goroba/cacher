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
    storage = RedisStringStorage()

    assert isinstance(storage, KeyValueStorage)
    assert storage.get(client, _NAME, "missing") is None
    assert storage.exists(client, _NAME, "missing") is False
    storage.delete(client, _NAME, "missing")

    storage.set(client, _NAME, "a", "1", ttl=10)
    assert storage.get(client, _NAME, "a") == "1"
    assert storage.exists(client, _NAME, "a") is True
    assert client.get("users:a") == "1"
    assert 0 < client.ttl("users:a") <= 10

    storage.mset(client, _NAME, {"b": "2", "c": "3"})
    assert client.ttl("users:b") == -1
    assert storage.mget(client, _NAME, ["b", "a", "b", "missing"]) == ["2", "1", "2", None]

    storage.mset(client, _NAME, {"b": "20", "c": "30"}, ttl=5)
    assert storage.get(client, _NAME, "b") == "20"
    assert client.get("users:b") == "20"
    assert client.get("users:c") == "30"
    assert 0 < client.ttl("users:b") <= 5
    assert 0 < client.ttl("users:c") <= 5

    storage.delete(client, _NAME, "a")
    assert storage.get(client, _NAME, "a") is None
    assert storage.exists(client, _NAME, "a") is False


def test_sync_storage_empty_batches_do_not_call_redis() -> None:
    spy = _MgetSpy()
    storage = RedisStringStorage()

    assert storage.mget(spy, _NAME, []) == []  # type: ignore[arg-type]
    storage.mset(spy, _NAME, {})  # type: ignore[arg-type]
    assert spy.called is False


def test_sync_storage_decodes_bytes() -> None:
    client = fakeredis.FakeRedis(decode_responses=False)
    storage = RedisStringStorage()

    storage.set(client, _NAME, "a", "hello")
    assert client.get("users:a") == b"hello"
    assert storage.get(client, _NAME, "a") == "hello"
    assert storage.mget(client, _NAME, ["a", "missing"]) == ["hello", None]


def test_async_storage_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        storage = AsyncRedisStringStorage()
        try:
            assert isinstance(storage, AsyncKeyValueStorage)
            assert await storage.get(client, _NAME, "missing") is None
            assert await storage.exists(client, _NAME, "missing") is False
            await storage.delete(client, _NAME, "missing")

            await storage.set(client, _NAME, "a", "1", ttl=10)
            assert await storage.get(client, _NAME, "a") == "1"
            assert await storage.exists(client, _NAME, "a") is True
            assert await client.get("users:a") == "1"
            assert 0 < await client.ttl("users:a") <= 10

            await storage.mset(client, _NAME, {"b": "2", "c": "3"})
            assert await client.ttl("users:b") == -1
            assert await storage.mget(client, _NAME, ["b", "a", "b", "missing"]) == [
                "2",
                "1",
                "2",
                None,
            ]

            await storage.mset(client, _NAME, {"b": "20", "c": "30"}, ttl=5)
            assert await storage.get(client, _NAME, "b") == "20"
            assert await client.get("users:b") == "20"
            assert await client.get("users:c") == "30"
            assert 0 < await client.ttl("users:b") <= 5
            assert 0 < await client.ttl("users:c") <= 5

            await storage.delete(client, _NAME, "a")
            assert await storage.get(client, _NAME, "a") is None
            assert await storage.exists(client, _NAME, "a") is False
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_async_storage_empty_batches_do_not_call_redis() -> None:
    spy = _MgetSpy()
    storage = AsyncRedisStringStorage()

    async def scenario() -> None:
        assert await storage.mget(spy, _NAME, []) == []  # type: ignore[arg-type]
        await storage.mset(spy, _NAME, {})  # type: ignore[arg-type]

    asyncio.run(scenario())
    assert spy.called is False


def test_async_storage_decodes_bytes() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=False)
        storage = AsyncRedisStringStorage()
        try:
            await storage.set(client, _NAME, "a", "hello")
            assert await client.get("users:a") == b"hello"
            assert await storage.get(client, _NAME, "a") == "hello"
            assert await storage.mget(client, _NAME, ["a", "missing"]) == ["hello", None]
        finally:
            await client.aclose()

    asyncio.run(scenario())
