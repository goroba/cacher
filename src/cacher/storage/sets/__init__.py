"""Set storage.

``SetStorage`` and ``AsyncSetStorage`` do not require Redis.
Importing a Redis storage class requires the ``redis`` extra.
"""

from cacher.storage.sets.async_storage import AsyncSetStorage
from cacher.storage.sets.storage import SetStorage

__all__ = [
    "AsyncRedisSetStorage",
    "AsyncSetStorage",
    "RedisSetStorage",
    "SetStorage",
]


def __getattr__(name: str) -> type:
    if name == "AsyncRedisSetStorage":
        from cacher.storage.sets.async_redis_set_storage import AsyncRedisSetStorage

        return AsyncRedisSetStorage
    if name == "RedisSetStorage":
        from cacher.storage.sets.redis_set_storage import RedisSetStorage

        return RedisSetStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
