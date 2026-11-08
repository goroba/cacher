"""Synchronous Redis hash storage."""

from collections.abc import Mapping, Sequence

from cacher.storage._redis import Redis, decode
from cacher.storage.key_value.storage import KeyValueStorage


class RedisHashStorage(KeyValueStorage[Redis, str, str]):
    """Synchronous Redis hashes. One instance can serve any hash name."""

    def get(self, client: Redis, name: str, field: str) -> str | None:
        return decode(client.hget(name, field))

    def set(
        self, client: Redis, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        client.hset(name, field, value)
        if ttl is not None:
            client.hexpire(name, ttl, field)

    def delete(self, client: Redis, name: str, field: str) -> None:
        client.hdel(name, field)

    def exists(self, client: Redis, name: str, field: str) -> bool:
        return bool(client.hexists(name, field))

    def mget(self, client: Redis, name: str, fields: Sequence[str]) -> list[str | None]:
        if not fields:
            return []
        raw_values = client.hmget(name, list(fields))
        return [decode(raw) for raw in raw_values]

    def mset(
        self, client: Redis, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        if not items:
            return
        mapping = dict(items)
        client.hset(name, mapping=mapping)
        if ttl is not None:
            client.hexpire(name, ttl, *mapping)
