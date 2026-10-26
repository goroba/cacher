"""Cacher."""

from importlib.metadata import PackageNotFoundError, version

from cacher.indexes import (
    AsyncKeyValueIndex,
    AsyncSetIndex,
    Index,
    KeyValueBase,
    KeyValueIndex,
    SetBase,
    SetIndex,
    build_async_key_value_index,
    build_async_set_index,
    build_key_value_index,
    build_set_index,
    get_async_index,
    get_index,
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
from cacher.storage import AsyncKeyValueStorage, AsyncSetStorage, KeyValueStorage, SetStorage

try:
    __version__ = version("cacher")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "AsyncKeyValueIndex",
    "AsyncKeyValueStorage",
    "AsyncSetIndex",
    "AsyncSetStorage",
    "BoolSerializer",
    "DataclassSerializer",
    "DatetimeSerializer",
    "DictSerializer",
    "FloatSerializer",
    "Index",
    "IntSerializer",
    "KeyValueBase",
    "KeyValueIndex",
    "KeyValueStorage",
    "Serializer",
    "SetBase",
    "SetIndex",
    "SetStorage",
    "StrSerializer",
    "__version__",
    "build_async_key_value_index",
    "build_async_set_index",
    "build_key_value_index",
    "build_set_index",
    "get_async_index",
    "get_index",
]
