"""Key-value storage engines.

``KeyValueEngine`` and ``AsyncKeyValueEngine`` do not require Redis.
Importing a Redis engine class requires the ``redis`` extra.
"""

from cacher.engines.key_value.async_engine import AsyncKeyValueEngine
from cacher.engines.key_value.engine import KeyValueEngine

__all__ = [
    "AsyncKeyValueEngine",
    "AsyncRedisHashEngine",
    "AsyncRedisStringEngine",
    "KeyValueEngine",
    "RedisHashEngine",
    "RedisStringEngine",
]


def __getattr__(name: str) -> type:
    if name == "AsyncRedisHashEngine":
        from cacher.engines.key_value.async_redis_hash_engine import AsyncRedisHashEngine

        return AsyncRedisHashEngine
    if name == "AsyncRedisStringEngine":
        from cacher.engines.key_value.async_redis_string_engine import AsyncRedisStringEngine

        return AsyncRedisStringEngine
    if name == "RedisHashEngine":
        from cacher.engines.key_value.redis_hash_engine import RedisHashEngine

        return RedisHashEngine
    if name == "RedisStringEngine":
        from cacher.engines.key_value.redis_string_engine import RedisStringEngine

        return RedisStringEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
