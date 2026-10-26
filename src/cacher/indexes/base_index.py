"""Shared index attributes and key registry."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TYPE_CHECKING, ClassVar

from cacher.engines.async_engine import AsyncEngine
from cacher.engines.engine import Engine
from cacher.serializers.serializer import Serializer

if TYPE_CHECKING:
    from cacher.indexes.async_index import AsyncIndex
    from cacher.indexes.index import Index

_sync_indexes: dict[str, type] = {}
_async_indexes: dict[str, type] = {}


class BaseIndex[IdType: Hashable, ModelType, StorageType]:
    """Identifier, model, serializer, storage key, and engine for an index.

    ``ModelType`` is unconstrained: a builtin such as ``int`` or any class.
    ``key`` names that model in storage. For a hash engine it is the hash name.
    ``engine`` is the storage engine instance. Fields are stored as ``str``.
    """

    identifier: type[IdType]
    model: type[ModelType]
    serializer: Serializer[ModelType, StorageType]
    key: str
    engine: Engine[str, StorageType] | AsyncEngine[str, StorageType]
    _registry: ClassVar[dict[str, type] | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if "key" not in cls.__dict__:
            return
        key = cls.__dict__["key"]
        if not isinstance(key, str):
            raise TypeError(f"{cls.__name__} key must be str, got {type(key).__name__}")
        registry = cls._registry
        if registry is None:
            raise TypeError(f"{cls.__name__} must subclass Index or AsyncIndex")
        if key in registry:
            raise ValueError(f"index key {key!r} is already registered")
        registry[key] = cls


def get_index(key: str) -> type[Index]:
    """Return the sync index class registered for ``key``."""
    try:
        return _sync_indexes[key]
    except KeyError:
        raise KeyError(f"no index registered for {key!r}") from None


def get_async_index(key: str) -> type[AsyncIndex]:
    """Return the async index class registered for ``key``."""
    try:
        return _async_indexes[key]
    except KeyError:
        raise KeyError(f"no async index registered for {key!r}") from None
