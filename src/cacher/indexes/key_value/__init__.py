"""Key-value indexes bind a model to key-value storage and register that binding by key."""

from cacher.indexes.key_value.async_index import AsyncKeyValueIndex
from cacher.indexes.key_value.base_index import get_async_key_value_index, get_key_value_index
from cacher.indexes.key_value.builder import build_async_key_value_index, build_key_value_index
from cacher.indexes.key_value.index import KeyValueIndex

__all__ = [
    "AsyncKeyValueIndex",
    "KeyValueIndex",
    "build_async_key_value_index",
    "build_key_value_index",
    "get_async_key_value_index",
    "get_key_value_index",
]
