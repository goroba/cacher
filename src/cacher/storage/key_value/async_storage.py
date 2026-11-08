"""Asynchronous key-value storage."""

from collections.abc import Hashable, Mapping, Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class AsyncKeyValueStorage[ClientType, FieldType: Hashable, StorageType](Protocol):
    """Asynchronous key-value storage.

    ``client`` is the storage client for that call.
    ``name`` is the storage name. ``field`` identifies one stored value.
    ``ttl`` is a whole number of seconds. ``None`` means the write does not expire.
    ``mset`` applies one TTL to every field.
    """

    async def get(self, client: ClientType, name: str, field: FieldType) -> StorageType | None:
        """Return the stored value, or ``None`` when the field is missing."""
        ...

    async def set(
        self,
        client: ClientType,
        name: str,
        field: FieldType,
        value: StorageType,
        *,
        ttl: int | None = None,
    ) -> None:
        """Store ``value`` under ``field``."""
        ...

    async def delete(self, client: ClientType, name: str, field: FieldType) -> None:
        """Remove ``field``. A missing field is not an error."""
        ...

    async def exists(self, client: ClientType, name: str, field: FieldType) -> bool:
        """Return whether ``field`` is present."""
        ...

    async def mget(
        self, client: ClientType, name: str, fields: Sequence[FieldType]
    ) -> list[StorageType | None]:
        """Return values in input order. Missing fields are ``None``."""
        ...

    async def mset(
        self,
        client: ClientType,
        name: str,
        items: Mapping[FieldType, StorageType],
        *,
        ttl: int | None = None,
    ) -> None:
        """Store every item. ``ttl`` applies to each field."""
        ...
