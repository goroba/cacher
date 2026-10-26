"""Asynchronous Redis set storage."""

from collections.abc import Sequence

from cacher.storage._redis import AsyncRedis
from cacher.storage.sets.async_storage import AsyncSetStorage


class AsyncRedisSetStorage(AsyncSetStorage[str]):
    """Asynchronous Redis sets. ``name`` is the Redis key."""

    def __init__(self, client: AsyncRedis) -> None:
        self._client = client

    async def add(self, name: str, member: str) -> None:
        await self._client.sadd(name, member)

    async def madd(self, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        await self._client.sadd(name, *members)

    async def remove(self, name: str, member: str) -> None:
        await self._client.srem(name, member)

    async def mremove(self, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        await self._client.srem(name, *members)

    async def contains(self, name: str, member: str) -> bool:
        return bool(await self._client.sismember(name, member))
