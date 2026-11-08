"""Asynchronous Redis set storage."""

from collections.abc import Sequence

from cacher.storage._redis import AsyncRedis
from cacher.storage.sets.async_storage import AsyncSetStorage


class AsyncRedisSetStorage(AsyncSetStorage[AsyncRedis, str]):
    """Asynchronous Redis sets. ``name`` is the Redis key."""

    async def add(self, client: AsyncRedis, name: str, member: str) -> None:
        await client.sadd(name, member)

    async def madd(self, client: AsyncRedis, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        await client.sadd(name, *members)

    async def remove(self, client: AsyncRedis, name: str, member: str) -> None:
        await client.srem(name, member)

    async def mremove(self, client: AsyncRedis, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        await client.srem(name, *members)

    async def contains(self, client: AsyncRedis, name: str, member: str) -> bool:
        return bool(await client.sismember(name, member))
