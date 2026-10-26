"""Storage engines.

``Engine`` and ``AsyncEngine`` do not require Redis.
Importing a Redis engine class requires the ``redis`` extra.
"""

from cacher.engines.async_engine import AsyncEngine
from cacher.engines.engine import Engine

__all__ = [
    "AsyncEngine",
    "AsyncRedisHashEngine",
    "AsyncRedisStringEngine",
    "Engine",
    "RedisHashEngine",
    "RedisStringEngine",
]


def __getattr__(name: str) -> type:
    if name == "AsyncRedisHashEngine":
        from cacher.engines.async_redis_hash_engine import AsyncRedisHashEngine

        return AsyncRedisHashEngine
    if name == "AsyncRedisStringEngine":
        from cacher.engines.async_redis_string_engine import AsyncRedisStringEngine

        return AsyncRedisStringEngine
    if name == "RedisHashEngine":
        from cacher.engines.redis_hash_engine import RedisHashEngine

        return RedisHashEngine
    if name == "RedisStringEngine":
        from cacher.engines.redis_string_engine import RedisStringEngine

        return RedisStringEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
