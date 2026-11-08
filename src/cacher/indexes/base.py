"""Shared index registration."""

from __future__ import annotations

from typing import ClassVar

from cacher.indexes.registry import IndexRegistry

_registries: dict[type, IndexRegistry] = {}


class Index:
    """Storage key and the registry that records an index.

    Indexes that share a storage client type share one registry.
    A subclass that defines ``key`` and ``client_type`` registers one instance.
    """

    key: str
    client_type: ClassVar[type]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if "key" not in cls.__dict__:
            return
        key = cls.__dict__["key"]
        if not isinstance(key, str):
            raise TypeError(f"{cls.__name__} key must be str, got {type(key).__name__}")
        client_type = getattr(cls, "client_type", None)
        if not isinstance(client_type, type):
            raise TypeError(f"{cls.__name__} must declare client_type as a class")
        registry = _registries.get(client_type)
        if registry is None:
            registry = IndexRegistry(client_type)
            _registries[client_type] = registry
        registry.set(key, cls())


def get_registry(client_type: type) -> IndexRegistry:
    """Return the registry of indexes for this storage client type."""
    try:
        return _registries[client_type]
    except KeyError:
        name = client_type.__name__ if isinstance(client_type, type) else repr(client_type)
        raise KeyError(f"no indexes registered for {name}") from None
