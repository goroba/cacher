import asyncio
from collections.abc import Sequence

import fakeredis

from cacher.engines import AsyncRedisSetEngine, RedisSetEngine
from cacher.engines.sets.async_engine import AsyncSetEngine
from cacher.engines.sets.engine import SetEngine


class _SetSpy:
    def __init__(self) -> None:
        self.called = False

    def sadd(self, name: str, *members: str) -> int:
        self.called = True
        return 0

    def srem(self, name: str, *members: str) -> int:
        self.called = True
        return 0


def test_sync_set_engine_round_trip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    engine = RedisSetEngine(client)
    assert isinstance(engine, SetEngine)

    assert engine.contains("users", "1") is False
    engine.remove("users", "1")
    assert engine.contains("users", "1") is False

    engine.add("users", "1")
    engine.add("users", "1")
    assert engine.contains("users", "1") is True
    assert client.sismember("users", "1") == 1

    engine.madd("users", ["3", "2"])
    assert engine.contains("users", "2") is True
    assert engine.contains("users", "3") is True
    assert client.smembers("users") == {"1", "2", "3"}

    engine.mremove("users", ["1", "3"])
    assert engine.contains("users", "1") is False
    assert engine.contains("users", "3") is False
    assert engine.contains("users", "2") is True
    engine.remove("users", "2")
    assert engine.contains("users", "2") is False


def test_sync_set_engine_empty_batches_do_not_call_redis() -> None:
    spy = _SetSpy()
    engine = RedisSetEngine(spy)  # type: ignore[arg-type]

    engine.madd("users", [])
    engine.mremove("users", [])
    assert spy.called is False


def test_async_set_engine_round_trip() -> None:
    async def scenario() -> None:
        client = fakeredis.FakeAsyncRedis(decode_responses=True)
        engine = AsyncRedisSetEngine(client)
        assert isinstance(engine, AsyncSetEngine)
        try:
            assert await engine.contains("users", "1") is False
            await engine.remove("users", "1")
            assert await engine.contains("users", "1") is False

            await engine.add("users", "1")
            await engine.add("users", "1")
            assert await engine.contains("users", "1") is True
            assert await client.sismember("users", "1") == 1

            await engine.madd("users", ["3", "2"])
            assert await engine.contains("users", "2") is True
            assert await engine.contains("users", "3") is True
            assert await client.smembers("users") == {"1", "2", "3"}

            await engine.mremove("users", ["1", "3"])
            assert await engine.contains("users", "1") is False
            assert await engine.contains("users", "3") is False
            assert await engine.contains("users", "2") is True
            await engine.remove("users", "2")
            assert await engine.contains("users", "2") is False
        finally:
            await client.aclose()

    asyncio.run(scenario())


def test_async_set_engine_empty_batches_do_not_call_redis() -> None:
    spy = _SetSpy()
    engine = AsyncRedisSetEngine(spy)  # type: ignore[arg-type]

    async def scenario() -> None:
        await engine.madd("users", [])
        await engine.mremove("users", [])

    asyncio.run(scenario())
    assert spy.called is False
