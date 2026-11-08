"""Synchronous Redis string storage."""

from collections.abc import Mapping, Sequence

from cacher.storage._redis import Redis, decode
from cacher.storage.key_value.storage import KeyValueStorage


def _redis_key(name: str, field: str) -> str:
    return f"{name}:{field}"


class RedisStringStorage(KeyValueStorage[Redis, str, str]):
    """Synchronous Redis strings. The Redis key is ``name:field``."""

    def get(self, client: Redis, name: str, field: str) -> str | None:
        return decode(client.get(_redis_key(name, field)))

    def set(
        self, client: Redis, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        key = _redis_key(name, field)
        if ttl is None:
            client.set(key, value)
        else:
            client.set(key, value, ex=ttl)

    def delete(self, client: Redis, name: str, field: str) -> None:
        client.delete(_redis_key(name, field))

    def exists(self, client: Redis, name: str, field: str) -> bool:
        return bool(client.exists(_redis_key(name, field)))

    def mget(self, client: Redis, name: str, fields: Sequence[str]) -> list[str | None]:
        if not fields:
            return []
        raw = client.mget([_redis_key(name, field) for field in fields])
        return [decode(item) for item in raw]

    def mset(
        self, client: Redis, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        if not items:
            return
        mapping = {_redis_key(name, field): value for field, value in items.items()}
        if ttl is None:
            client.mset(mapping)
            return
        pipe = client.pipeline(transaction=True)
        for key, value in mapping.items():
            pipe.set(key, value, ex=ttl)
        pipe.execute()
