"""Shared key-value index attributes and key registry."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TYPE_CHECKING, ClassVar

from cacher.engines.key_value.async_engine import AsyncKeyValueEngine
from cacher.engines.key_value.engine import KeyValueEngine
from cacher.serializers.serializer import Serializer

if TYPE_CHECKING:
    from cacher.indexes.key_value.async_index import AsyncKeyValueIndex
    from cacher.indexes.key_value.index import KeyValueIndex

_sync_indexes: dict[str, type] = {}
_async_indexes: dict[str, type] = {}


class _KeyValueBase[IdType: Hashable, ModelType, StorageType]:
    """Identifier, model, serializer, storage key, and engine for a key-value index.

    ``ModelType`` is unconstrained: a builtin such as ``int`` or any class.
    ``key`` names that model in storage. For a hash engine it is the hash name.
    ``engine`` is the key-value engine instance. Fields are stored as ``str``.
    """

    identifier: type[IdType]
    model: type[ModelType]
    serializer: Serializer[ModelType, StorageType]
    key: str
    engine: KeyValueEngine[str, StorageType] | AsyncKeyValueEngine[str, StorageType]
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
            raise TypeError(f"{cls.__name__} must subclass KeyValueIndex or AsyncKeyValueIndex")
        if key in registry:
            raise ValueError(f"index key {key!r} is already registered")
        registry[key] = cls


def get_key_value_index(key: str) -> type[KeyValueIndex]:
    """Return the sync key-value index class registered for ``key``."""
    try:
        return _sync_indexes[key]
    except KeyError:
        raise KeyError(f"no key-value index registered for {key!r}") from None


def get_async_key_value_index(key: str) -> type[AsyncKeyValueIndex]:
    """Return the async key-value index class registered for ``key``."""
    try:
        return _async_indexes[key]
    except KeyError:
        raise KeyError(f"no async key-value index registered for {key!r}") from None
