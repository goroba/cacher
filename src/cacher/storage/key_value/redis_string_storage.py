"""Synchronous Redis string storage."""

from collections.abc import Mapping, Sequence

from cacher.storage._redis import Redis, decode
from cacher.storage.key_value.storage import KeyValueStorage


def _redis_key(name: str, field: str) -> str:
    return f"{name}:{field}"


class RedisStringStorage(KeyValueStorage[str, str]):
    """Synchronous Redis strings. The Redis key is ``name:field``."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    def get(self, name: str, field: str) -> str | None:
        return decode(self._client.get(_redis_key(name, field)))

    def set(self, name: str, field: str, value: str, *, ttl: int | None = None) -> None:
        key = _redis_key(name, field)
        if ttl is None:
            self._client.set(key, value)
        else:
            self._client.set(key, value, ex=ttl)

    def delete(self, name: str, field: str) -> None:
        self._client.delete(_redis_key(name, field))

    def exists(self, name: str, field: str) -> bool:
        return bool(self._client.exists(_redis_key(name, field)))

    def mget(self, name: str, fields: Sequence[str]) -> list[str | None]:
        if not fields:
            return []
        raw = self._client.mget([_redis_key(name, field) for field in fields])
        return [decode(item) for item in raw]

    def mset(self, name: str, items: Mapping[str, str], *, ttl: int | None = None) -> None:
        if not items:
            return
        mapping = {_redis_key(name, field): value for field, value in items.items()}
        if ttl is None:
            self._client.mset(mapping)
            return
        pipe = self._client.pipeline(transaction=True)
        for key, value in mapping.items():
            pipe.set(key, value, ex=ttl)
        pipe.execute()
