"""Synchronous Redis set engine."""

from collections.abc import Sequence

from cacher.engines._redis import Redis
from cacher.engines.sets.engine import SetEngine


class RedisSetEngine(SetEngine[str]):
    """Synchronous Redis sets. ``name`` is the Redis key."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    def add(self, name: str, member: str) -> None:
        self._client.sadd(name, member)

    def madd(self, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        self._client.sadd(name, *members)

    def remove(self, name: str, member: str) -> None:
        self._client.srem(name, member)

    def mremove(self, name: str, members: Sequence[str]) -> None:
        if not members:
            return
        self._client.srem(name, *members)

    def contains(self, name: str, member: str) -> bool:
        return bool(self._client.sismember(name, member))
