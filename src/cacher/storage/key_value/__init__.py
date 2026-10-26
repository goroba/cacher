"""Key-value storage.

``KeyValueStorage`` and ``AsyncKeyValueStorage`` do not require Redis.
Importing a Redis storage class requires the ``redis`` extra.
"""

from cacher.storage.key_value.async_storage import AsyncKeyValueStorage
from cacher.storage.key_value.storage import KeyValueStorage

__all__ = [
    "AsyncKeyValueStorage",
    "AsyncRedisHashStorage",
    "AsyncRedisStringStorage",
    "KeyValueStorage",
    "RedisHashStorage",
    "RedisStringStorage",
]


def __getattr__(name: str) -> type:
    if name == "AsyncRedisHashStorage":
        from cacher.storage.key_value.async_redis_hash_storage import AsyncRedisHashStorage

        return AsyncRedisHashStorage
    if name == "AsyncRedisStringStorage":
        from cacher.storage.key_value.async_redis_string_storage import AsyncRedisStringStorage

        return AsyncRedisStringStorage
    if name == "RedisHashStorage":
        from cacher.storage.key_value.redis_hash_storage import RedisHashStorage

        return RedisHashStorage
    if name == "RedisStringStorage":
        from cacher.storage.key_value.redis_string_storage import RedisStringStorage

        return RedisStringStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
