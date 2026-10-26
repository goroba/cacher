import asyncio
from collections.abc import Sequence

import fakeredis

from cacher.engines import AsyncRedisStringEngine, RedisStringEngine
from cacher.engines.key_value.async_engine import AsyncKeyValueEngine
from cacher.engines.key_value.engine import KeyValueEngine

_NAME = "users"


class _MgetSpy:
    def __init__(self) -> None:
        self.called = False

    def mget(self, keys: Sequence[str]) -> list[str | None]:
        self.called = True
        return [None for _ in keys]

    def mset(self, items: dict[str, str]) -> None:
        self.called = True


def test_sync_engine_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    engine = RedisStringEngine(client)

    assert isinstance(engine, KeyValueEngine)
    assert engine.get(_NAME, "missing") is None
    assert engine.exists(_NAME, "missing") is False
    engine.delete(_NAME, "missing")

    engine.set(_NAME, "a", "1", ttl=10)
    assert engine.get(_NAME, "a") == "1"
    assert engine.exists(_NAME, "a") is True
    assert client.get("users:a") == "1"
    assert 0 < client.ttl("users:a") <= 10

    engine.mset(_NAME, {"b": "2", "c": "3"})
    assert client.ttl("users:b") == -1
    assert engine.mget(_NAME, ["b", "a", "b", "missing"]) == ["2", "1", "2", None]

    engine.mset(_NAME, {"b": "20", "c": "30"}, ttl=5)
    assert engine.get(_NAME, "b") == "20"
    assert client.get("users:b") == "20"
    assert client.get("users:c") == "30"
    assert 0 < client.ttl("users:b") <= 5
    assert 0 < client.ttl("users:c") <= 5

    engine.delete(_NAME, "a")
    assert engine.get(_NAME, "a") is None
    assert engine.exists(_NAME, "a") is False


def test_sync_engine_empty_batches_do_not_call_redis() -> None:
    spy = _MgetSpy()
    engine = RedisStringEngine(spy)  # type: ignore[arg-type]

    assert engine.mget(_NAME, []) == []
    engine.mset(_NAME, {})
    assert spy.called is False


def test_sync_engine_decodes_bytes() -> None:
    client = fakeredis.FakeRedis(decode_responses=False)
    engine = RedisStringEngine(client)

    engine.set(_NAME, "a", "hello")
    assert client.get("users:a") == b"hello"
    assert engine.get(_NAME, "a") == "hello"
    assert engine.mget(_NAME, ["a", "missing"]) == ["hello", None]


def test_async_engine_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        engine = AsyncRedisStringEngine(client)
        try:
            assert isinstance(engine, AsyncKeyValueEngine)
            assert await engine.get(_NAME, "missing") is None
            assert await engine.exists(_NAME, "missing") is False
            await engine.delete(_NAME, "missing")

            await engine.set(_NAME, "a", "1", ttl=10)
            assert await engine.get(_NAME, "a") == "1"
            assert await engine.exists(_NAME, "a") is True
            assert await client.get("users:a") == "1"
            assert 0 < await client.ttl("users:a") <= 10

            await engine.mset(_NAME, {"b": "2", "c": "3"})
            assert await client.ttl("users:b") == -1
            assert await engine.mget(_NAME, ["b", "a", "b", "missing"]) == ["2", "1", "2", None]

            await engine.mset(_NAME, {"b": "20", "c": "30"}, ttl=5)
            assert await engine.get(_NAME, "b") == "20"
            assert await client.get("users:b") == "20"
            assert await client.get("users:c") == "30"
            assert 0 < await client.ttl("users:b") <= 5
            assert 0 < await client.ttl("users:c") <= 5

            await engine.delete(_NAME, "a")
            assert await engine.get(_NAME, "a") is None
            assert await engine.exists(_NAME, "a") is False
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_async_engine_empty_batches_do_not_call_redis() -> None:
    spy = _MgetSpy()
    engine = AsyncRedisStringEngine(spy)  # type: ignore[arg-type]

    async def scenario() -> None:
        assert await engine.mget(_NAME, []) == []
        await engine.mset(_NAME, {})

    asyncio.run(scenario())
    assert spy.called is False


def test_async_engine_decodes_bytes() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=False)
        engine = AsyncRedisStringEngine(client)
        try:
            await engine.set(_NAME, "a", "hello")
            assert await client.get("users:a") == b"hello"
            assert await engine.get(_NAME, "a") == "hello"
            assert await engine.mget(_NAME, ["a", "missing"]) == ["hello", None]
        finally:
            await client.aclose()

    asyncio.run(scenario())
