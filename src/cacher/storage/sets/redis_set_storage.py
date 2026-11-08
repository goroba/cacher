"""Synchronous Redis set storage."""

from collections.abc import Sequence

from cacher.storage._redis import Redis
from cacher.storage.sets.storage import SetStorage


class RedisSetStorage(SetStorage[Redis, str]):
    """Synchronous Redis sets. ``name`` is the Redis key."""

    def add(self, client: Redis, name: str, member: str) -> None:
        client.sadd(name, member)

    def madd(self, client: Redis, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        client.sadd(name, *members)

    def remove(self, client: Redis, name: str, member: str) -> None:
        client.srem(name, member)

    def mremove(self, client: Redis, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        client.srem(name, *members)

    def contains(self, client: Redis, name: str, member: str) -> bool:
        return bool(client.sismember(name, member))
