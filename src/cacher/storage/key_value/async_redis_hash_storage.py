"""Asynchronous Redis hash storage."""

from collections.abc import Mapping, Sequence

from cacher.storage._redis import AsyncRedis, decode
from cacher.storage.key_value.async_storage import AsyncKeyValueStorage


class AsyncRedisHashStorage(AsyncKeyValueStorage[str, str]):
    """Asynchronous Redis hashes. One instance can serve any hash name."""

    def __init__(self, client: AsyncRedis) -> None:
        self._client = client

    async def get(self, name: str, field: str) -> str | None:
        return decode(await self._client.hget(name, field))

    async def set(self, name: str, field: str, value: str, *, ttl: int | None = None) -> None:
        await self._client.hset(name, field, value)
        if ttl is not None:
            await self._client.hexpire(name, ttl, field)

    async def delete(self, name: str, field: str) -> None:
        await self._client.hdel(name, field)

    async def exists(self, name: str, field: str) -> bool:
        return bool(await self._client.hexists(name, field))

    async def mget(self, name: str, fields: Sequence[str]) -> list[str | None]:
        if not fields:
            return []
        raw_values = await self._client.hmget(name, list(fields))
        return [decode(raw) for raw in raw_values]

    async def mset(self, name: str, items: Mapping[str, str], *, ttl: int | None = None) -> None:
        if not items:
            return
        mapping = dict(items)
        await self._client.hset(name, mapping=mapping)
        if ttl is not None:
            await self._client.hexpire(name, ttl, *mapping)
