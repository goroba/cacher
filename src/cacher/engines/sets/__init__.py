"""Set storage engines.

``SetEngine`` and ``AsyncSetEngine`` do not require Redis.
Importing a Redis engine class requires the ``redis`` extra.
"""

from cacher.engines.sets.async_engine import AsyncSetEngine
from cacher.engines.sets.engine import SetEngine

__all__ = [
    "AsyncRedisSetEngine",
    "AsyncSetEngine",
    "RedisSetEngine",
    "SetEngine",
]


def __getattr__(name: str) -> type:
    if name == "AsyncRedisSetEngine":
        from cacher.engines.sets.async_redis_set_engine import AsyncRedisSetEngine

        return AsyncRedisSetEngine
    if name == "RedisSetEngine":
        from cacher.engines.sets.redis_set_engine import RedisSetEngine

        return RedisSetEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
