"""Indexes bind a value to storage and register that binding by key."""

from cacher.indexes.base import Index, get_registry
from cacher.indexes.key_value import (
    AsyncKeyValueIndex,
    KeyValueBase,
    KeyValueIndex,
    build_async_key_value_index,
    build_key_value_index,
)
from cacher.indexes.registry import IndexRegistry
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
    "IndexRegistry",
    "KeyValueBase",
    "KeyValueIndex",
    "SetBase",
    "SetIndex",
    "build_async_key_value_index",
    "build_async_set_index",
    "build_key_value_index",
    "build_set_index",
    "get_registry",
]
