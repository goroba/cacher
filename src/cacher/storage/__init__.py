"""Storage.

Protocols do not require Redis. Importing a Redis storage class requires the ``redis`` extra.
"""

import importlib

from cacher.storage.key_value import AsyncKeyValueStorage, KeyValueStorage
from cacher.storage.sets import AsyncSetStorage, SetStorage

__all__ = [
    "AsyncKeyValueStorage",
    "AsyncRedisHashStorage",
    "AsyncRedisSetStorage",
    "AsyncRedisStringStorage",
    "AsyncSetStorage",
    "KeyValueStorage",
    "RedisHashStorage",
    "RedisSetStorage",
    "RedisStringStorage",
    "SetStorage",
]

_KEY_VALUE = {
    "AsyncRedisHashStorage",
    "AsyncRedisStringStorage",
    "RedisHashStorage",
    "RedisStringStorage",
}
_SETS = {
    "AsyncRedisSetStorage",
    "RedisSetStorage",
}


def __getattr__(name: str) -> type:
    if name in _KEY_VALUE:
        module = importlib.import_module("cacher.storage.key_value")
        return getattr(module, name)
    if name in _SETS:
        module = importlib.import_module("cacher.storage.sets")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
