"""Shared set index attributes and key registry."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TYPE_CHECKING, ClassVar

from cacher.engines.sets.async_engine import AsyncSetEngine
from cacher.engines.sets.engine import SetEngine
from cacher.serializers.serializer import Serializer

if TYPE_CHECKING:
    from cacher.indexes.sets.async_index import AsyncSetIndex
    from cacher.indexes.sets.index import SetIndex

_sync_indexes: dict[str, type] = {}
_async_indexes: dict[str, type] = {}


class _SetBase[MemberType, StorageType: Hashable]:
    """Member, serializer, storage key, and engine for a set index.

    ``key`` is the set name. ``engine`` stores serialized members.
    """

    member: type[MemberType]
    serializer: Serializer[MemberType, StorageType]
    key: str
    engine: SetEngine[StorageType] | AsyncSetEngine[StorageType]
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
            raise TypeError(f"{cls.__name__} must subclass SetIndex or AsyncSetIndex")
        if key in registry:
            raise ValueError(f"index key {key!r} is already registered")
        registry[key] = cls


def get_set_index(key: str) -> type[SetIndex]:
    """Return the sync set index class registered for ``key``."""
    try:
        return _sync_indexes[key]
    except KeyError:
        raise KeyError(f"no set index registered for {key!r}") from None


def get_async_set_index(key: str) -> type[AsyncSetIndex]:
    """Return the async set index class registered for ``key``."""
    try:
        return _async_indexes[key]
    except KeyError:
        raise KeyError(f"no async set index registered for {key!r}") from None
