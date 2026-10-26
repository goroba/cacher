"""Synchronous Redis hash engine."""

from collections.abc import Mapping, Sequence

from cacher.engines._redis import Redis, decode
from cacher.engines.engine import Engine


class RedisHashEngine(Engine[str, str]):
    """Synchronous Redis hashes. One instance can serve any hash name."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    def get(self, name: str, field: str) -> str | None:
        return decode(self._client.hget(name, field))

    def set(self, name: str, field: str, value: str, *, ttl: int | None = None) -> None:
        self._client.hset(name, field, value)
        if ttl is not None:
            self._client.hexpire(name, ttl, field)

    def delete(self, name: str, field: str) -> None:
        self._client.hdel(name, field)

    def exists(self, name: str, field: str) -> bool:
        return bool(self._client.hexists(name, field))

    def mget(self, name: str, fields: Sequence[str]) -> list[str | None]:
        if not fields:
            return []
        raw_values = self._client.hmget(name, list(fields))
        return [decode(raw) for raw in raw_values]

    def mset(self, name: str, items: Mapping[str, str], *, ttl: int | None = None) -> None:
        if not items:
            return
        mapping = dict(items)
        self._client.hset(name, mapping=mapping)
        if ttl is not None:
            self._client.hexpire(name, ttl, *mapping)
