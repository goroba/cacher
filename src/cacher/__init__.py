"""Cacher."""

from importlib.metadata import PackageNotFoundError, version

from cacher.engines import AsyncKeyValueEngine, AsyncSetEngine, KeyValueEngine, SetEngine
from cacher.indexes import (
    AsyncKeyValueIndex,
    AsyncSetIndex,
    KeyValueIndex,
    SetIndex,
    build_async_key_value_index,
    build_async_set_index,
    build_key_value_index,
    build_set_index,
    get_async_key_value_index,
    get_async_set_index,
    get_key_value_index,
    get_set_index,
)
from cacher.serializers import (
    BoolSerializer,
    DataclassSerializer,
    DatetimeSerializer,
    DictSerializer,
    FloatSerializer,
    IntSerializer,
    Serializer,
    StrSerializer,
)

try:
    __version__ = version("cacher")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "AsyncKeyValueEngine",
    "AsyncKeyValueIndex",
    "AsyncSetEngine",
    "AsyncSetIndex",
    "BoolSerializer",
    "DataclassSerializer",
    "DatetimeSerializer",
    "DictSerializer",
    "FloatSerializer",
    "IntSerializer",
    "KeyValueEngine",
    "KeyValueIndex",
    "Serializer",
    "SetEngine",
    "SetIndex",
    "StrSerializer",
    "__version__",
    "build_async_key_value_index",
    "build_async_set_index",
    "build_key_value_index",
    "build_set_index",
    "get_async_key_value_index",
    "get_async_set_index",
    "get_key_value_index",
    "get_set_index",
]
