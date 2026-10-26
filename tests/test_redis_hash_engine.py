import asyncio
from collections.abc import Sequence

import fakeredis

from cacher.engines.async_engine import AsyncEngine
from cacher.engines.async_redis_hash_engine import AsyncRedisHashEngine
from cacher.engines.engine import Engine
from cacher.engines.redis_hash_engine import RedisHashEngine


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


def test_sync_hash_engine_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    engine = RedisHashEngine(client)
    assert isinstance(engine, Engine)

    assert engine.get("users", "1") is None
    assert engine.exists("users", "1") is False
    engine.delete("users", "1")

    engine.set("users", "1", "10", ttl=30)
    assert engine.get("users", "1") == "10"
    assert engine.exists("users", "1") is True
    assert 0 < client.httl("users", "1")[0] <= 30

    engine.mset("users", {"2": "20", "3": "30"})
    assert engine.mget("users", ["2", "1", "2", "9"]) == ["20", "10", "20", None]
    assert client.httl("users", "2")[0] == -1

    engine.mset("users", {"2": "21", "4": "40"}, ttl=5)
    assert engine.get("users", "2") == "21"
    assert 0 < client.httl("users", "2")[0] <= 5
    assert 0 < client.httl("users", "4")[0] <= 5
    assert client.httl("users", "1")[0] > 5

    engine.delete("users", "1")
    assert engine.get("users", "1") is None
    assert engine.exists("users", "1") is False


def test_sync_hash_engine_empty_batches_do_not_call_redis() -> None:
    spy = _HashSpy()
    engine = RedisHashEngine(spy)  # type: ignore[arg-type]

    assert engine.mget("users", []) == []
    engine.mset("users", {})
    assert spy.hmget_called is False
    assert spy.hset_called is False


def test_sync_hash_engine_decodes_bytes() -> None:
    client = fakeredis.FakeRedis(decode_responses=False)
    engine = RedisHashEngine(client)

    engine.set("users", "1", "10")
    assert client.hget("users", "1") == b"10"
    assert engine.get("users", "1") == "10"
    assert engine.mget("users", ["1", "2"]) == ["10", None]


def test_async_hash_engine_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        engine = AsyncRedisHashEngine(client)
        assert isinstance(engine, AsyncEngine)
        try:
            assert await engine.get("users", "1") is None
            assert await engine.exists("users", "1") is False
            await engine.delete("users", "1")

            await engine.set("users", "1", "10", ttl=30)
            assert await engine.get("users", "1") == "10"
            assert await engine.exists("users", "1") is True
            assert 0 < (await client.httl("users", "1"))[0] <= 30

            await engine.mset("users", {"2": "20", "3": "30"})
            assert await engine.mget("users", ["2", "1", "2", "9"]) == ["20", "10", "20", None]
            assert (await client.httl("users", "2"))[0] == -1

            await engine.mset("users", {"2": "21", "4": "40"}, ttl=5)
            assert await engine.get("users", "2") == "21"
            assert 0 < (await client.httl("users", "2"))[0] <= 5
            assert 0 < (await client.httl("users", "4"))[0] <= 5
            assert (await client.httl("users", "1"))[0] > 5

            await engine.delete("users", "1")
            assert await engine.get("users", "1") is None
            assert await engine.exists("users", "1") is False
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_async_hash_engine_empty_batches_do_not_call_redis() -> None:
    spy = _HashSpy()
    engine = AsyncRedisHashEngine(spy)  # type: ignore[arg-type]

    async def scenario() -> None:
        assert await engine.mget("users", []) == []
        await engine.mset("users", {})

    asyncio.run(scenario())
    assert spy.hmget_called is False
    assert spy.hset_called is False


def test_async_hash_engine_decodes_bytes() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=False)
        engine = AsyncRedisHashEngine(client)
        try:
            await engine.set("users", "1", "10")
            assert await client.hget("users", "1") == b"10"
            assert await engine.get("users", "1") == "10"
            assert await engine.mget("users", ["1", "2"]) == ["10", None]
        finally:
            await client.aclose()

    asyncio.run(scenario())
