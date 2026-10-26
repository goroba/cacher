"""Cacher."""

from importlib.metadata import PackageNotFoundError, version

from cacher.engines import AsyncEngine, Engine
from cacher.indexes import (
    AsyncIndex,
    BaseIndex,
    Index,
    build_async_index,
    build_index,
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

try:
    __version__ = version("cacher")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "AsyncEngine",
    "AsyncIndex",
    "BaseIndex",
    "BoolSerializer",
    "DataclassSerializer",
    "DatetimeSerializer",
    "DictSerializer",
    "Engine",
    "FloatSerializer",
    "Index",
    "IntSerializer",
    "Serializer",
    "StrSerializer",
    "__version__",
    "build_async_index",
    "build_index",
    "get_async_index",
    "get_index",
]
