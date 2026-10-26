"""Indexes bind a value to storage and register that binding by key."""

from cacher.indexes.base import Index, get_async_index, get_index
from cacher.indexes.key_value import (
    AsyncKeyValueIndex,
    KeyValueBase,
    KeyValueIndex,
    build_async_key_value_index,
    build_key_value_index,
)
from cacher.indexes.sets import (
    AsyncSetIndex,
    SetBase,
    SetIndex,
    build_async_set_index,
    build_set_index,
)

__all__ = [
    "AsyncKeyValueIndex",
    "AsyncSetIndex",
    "Index",
    "KeyValueBase",
    "KeyValueIndex",
    "SetBase",
    "SetIndex",
    "build_async_key_value_index",
    "build_async_set_index",
    "build_key_value_index",
    "build_set_index",
    "get_async_index",
    "get_index",
]
