"""Storage engines.

Protocols do not require Redis. Importing a Redis engine class requires the ``redis`` extra.
"""

import importlib

from cacher.engines.key_value import AsyncKeyValueEngine, KeyValueEngine
from cacher.engines.sets import AsyncSetEngine, SetEngine

__all__ = [
    "AsyncKeyValueEngine",
    "AsyncRedisHashEngine",
    "AsyncRedisSetEngine",
    "AsyncRedisStringEngine",
    "AsyncSetEngine",
    "KeyValueEngine",
    "RedisHashEngine",
    "RedisSetEngine",
    "RedisStringEngine",
    "SetEngine",
]

_KEY_VALUE = {
    "AsyncRedisHashEngine",
    "AsyncRedisStringEngine",
    "RedisHashEngine",
    "RedisStringEngine",
}
_SETS = {
    "AsyncRedisSetEngine",
    "RedisSetEngine",
}


def __getattr__(name: str) -> type:
    if name in _KEY_VALUE:
        module = importlib.import_module("cacher.engines.key_value")
        return getattr(module, name)
    if name in _SETS:
        module = importlib.import_module("cacher.engines.sets")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
