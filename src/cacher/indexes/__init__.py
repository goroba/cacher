"""Indexes bind a model to storage and register that binding by key."""

from cacher.indexes.async_index import AsyncIndex
from cacher.indexes.base_index import BaseIndex, get_async_index, get_index
from cacher.indexes.builder import build_async_index, build_index
from cacher.indexes.index import Index

__all__ = [
    "AsyncIndex",
    "BaseIndex",
    "Index",
    "build_async_index",
    "build_index",
    "get_async_index",
    "get_index",
]
