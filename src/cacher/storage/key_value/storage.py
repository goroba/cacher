"""Synchronous key-value storage."""

from collections.abc import Hashable, Mapping, Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class KeyValueStorage[FieldType: Hashable, StorageType](Protocol):
    """Synchronous key-value storage.

    ``name`` is the storage name. ``field`` identifies one stored value.
    ``ttl`` is a whole number of seconds. ``None`` means the write does not expire.
    ``mset`` applies one TTL to every field.
    """

    def get(self, name: str, field: FieldType) -> StorageType | None:
        """Return the stored value, or ``None`` when the field is missing."""
        ...

    def set(
        self, name: str, field: FieldType, value: StorageType, *, ttl: int | None = None
    ) -> None:
        """Store ``value`` under ``field``."""
        ...

    def delete(self, name: str, field: FieldType) -> None:
        """Remove ``field``. A missing field is not an error."""
        ...

    def exists(self, name: str, field: FieldType) -> bool:
        """Return whether ``field`` is present."""
        ...

    def mget(self, name: str, fields: Sequence[FieldType]) -> list[StorageType | None]:
        """Return values in input order. Missing fields are ``None``."""
        ...

    def mset(
        self, name: str, items: Mapping[FieldType, StorageType], *, ttl: int | None = None
    ) -> None:
        """Store every item. ``ttl`` applies to each field."""
        ...
