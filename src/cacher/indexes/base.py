"""Shared index registration."""

from __future__ import annotations

from typing import ClassVar

_sync_indexes: dict[str, type[Index]] = {}
_async_indexes: dict[str, type[Index]] = {}


class Index:
    """Storage key and the registry that records an index class.

    Sync indexes share ``_sync_indexes``. Async indexes share ``_async_indexes``.
    """

    key: str
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
            raise TypeError(
                f"{cls.__name__} must subclass KeyValueIndex, AsyncKeyValueIndex, "
                "SetIndex, or AsyncSetIndex"
            )
        if key in registry:
            raise ValueError(f"index key {key!r} is already registered")
        registry[key] = cls


def get_index(key: str) -> type[Index]:
    """Return the sync index class registered for ``key``."""
    try:
        return _sync_indexes[key]
    except KeyError:
        raise KeyError(f"no index registered for {key!r}") from None


def get_async_index(key: str) -> type[Index]:
    """Return the async index class registered for ``key``."""
    try:
        return _async_indexes[key]
    except KeyError:
        raise KeyError(f"no async index registered for {key!r}") from None
