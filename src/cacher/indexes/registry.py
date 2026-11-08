"""Indexes registered for one storage client type."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cacher.indexes.base import Index


class IndexRegistry:
    """Indexes that share one storage client type."""

    def __init__(self, client_type: type) -> None:
        self.client_type = client_type
        self._indexes: dict[str, Index] = {}

    def get(self, name: str) -> Index:
        """Return the index registered under this name."""
        try:
            return self._indexes[name]
        except KeyError:
            raise KeyError(
                f"no index {name!r} registered for {self.client_type.__name__}"
            ) from None

    def set(self, name: str, index: Index) -> None:
        """Register an index under this name."""
        if name in self._indexes:
            raise ValueError(f"index key {name!r} is already registered")
        self._indexes[name] = index

    def __contains__(self, name: object) -> bool:
        return name in self._indexes

    def __iter__(self) -> Iterator[str]:
        return iter(self._indexes)
