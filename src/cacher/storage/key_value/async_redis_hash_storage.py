"""Asynchronous Redis hash storage."""

from collections.abc import Mapping, Sequence

from cacher.storage._redis import AsyncRedis, decode
from cacher.storage.key_value.async_storage import AsyncKeyValueStorage


class AsyncRedisHashStorage(AsyncKeyValueStorage[AsyncRedis, str, str]):
    """Asynchronous Redis hashes. One instance can serve any hash name."""

    async def get(self, client: AsyncRedis, name: str, field: str) -> str | None:
        return decode(await client.hget(name, field))

    async def set(
        self, client: AsyncRedis, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        await client.hset(name, field, value)
        if ttl is not None:
            await client.hexpire(name, ttl, field)

    async def delete(self, client: AsyncRedis, name: str, field: str) -> None:
        await client.hdel(name, field)

    async def exists(self, client: AsyncRedis, name: str, field: str) -> bool:
        return bool(await client.hexists(name, field))

    async def mget(self, client: AsyncRedis, name: str, fields: Sequence[str]) -> list[str | None]:
        if not fields:
            return []
        raw_values = await client.hmget(name, list(fields))
        return [decode(raw) for raw in raw_values]

    async def mset(
        self, client: AsyncRedis, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        if not items:
            return
        mapping = dict(items)
        await client.hset(name, mapping=mapping)
        if ttl is not None:
            await client.hexpire(name, ttl, *mapping)
