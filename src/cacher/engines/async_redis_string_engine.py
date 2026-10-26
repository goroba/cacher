"""Asynchronous Redis string engine."""

from collections.abc import Mapping, Sequence

from cacher.engines._redis import AsyncRedis, decode
from cacher.engines.async_engine import AsyncEngine


def _redis_key(name: str, field: str) -> str:
    return f"{name}:{field}"


class AsyncRedisStringEngine(AsyncEngine[str, str]):
    """Asynchronous Redis strings. The Redis key is ``name:field``."""

    def __init__(self, client: AsyncRedis) -> None:
        self._client = client

    async def get(self, name: str, field: str) -> str | None:
        return decode(await self._client.get(_redis_key(name, field)))

    async def set(self, name: str, field: str, value: str, *, ttl: int | None = None) -> None:
        key = _redis_key(name, field)
        if ttl is None:
            await self._client.set(key, value)
        else:
            await self._client.set(key, value, ex=ttl)

    async def delete(self, name: str, field: str) -> None:
        await self._client.delete(_redis_key(name, field))

    async def exists(self, name: str, field: str) -> bool:
        return bool(await self._client.exists(_redis_key(name, field)))

    async def mget(self, name: str, fields: Sequence[str]) -> list[str | None]:
        if not fields:
            return []
        raw = await self._client.mget([_redis_key(name, field) for field in fields])
        return [decode(item) for item in raw]

    async def mset(self, name: str, items: Mapping[str, str], *, ttl: int | None = None) -> None:
        if not items:
            return
        mapping = {_redis_key(name, field): value for field, value in items.items()}
        if ttl is None:
            await self._client.mset(mapping)
            return
        pipe = self._client.pipeline(transaction=True)
        for key, value in mapping.items():
            pipe.set(key, value, ex=ttl)
        await pipe.execute()
