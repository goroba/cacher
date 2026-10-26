"""Asynchronous key-value index."""

from collections.abc import Hashable, Mapping, Sequence

from cacher.indexes.base import _async_indexes
from cacher.indexes.key_value.base_index import KeyValueBase
from cacher.storage.key_value.async_storage import AsyncKeyValueStorage


class AsyncKeyValueIndex[IdType: Hashable, ModelType, StorageType](
    KeyValueBase[IdType, ModelType, StorageType]
):
    """Async key-value index: model binding, storage key, and the storage that persists it.

    Reads deserialize and writes serialize. The identifier is stored as ``str(id)``.
    """

    storage: AsyncKeyValueStorage[str, StorageType]
    _registry = _async_indexes

    async def get(self, id: IdType) -> ModelType | None:
        """Return the cached model, or ``None`` when the id is missing."""
        raw = await self.storage.get(self.key, str(id))
        if raw is None:
            return None
        return self.serializer.deserialize(raw)

    async def set(self, id: IdType, value: ModelType, *, ttl: int | None = None) -> None:
        """Store ``value`` under ``id``."""
        await self.storage.set(self.key, str(id), self.serializer.serialize(value), ttl=ttl)

    async def delete(self, id: IdType) -> None:
        """Remove ``id``. A missing id is not an error."""
        await self.storage.delete(self.key, str(id))

    async def exists(self, id: IdType) -> bool:
        """Return whether ``id`` is present."""
        return await self.storage.exists(self.key, str(id))

    async def mget(self, ids: Sequence[IdType]) -> list[ModelType | None]:
        """Return models in input order. Missing ids are ``None``."""
        if not ids:
            return []
        raw_values = await self.storage.mget(self.key, [str(id) for id in ids])
        return [None if raw is None else self.serializer.deserialize(raw) for raw in raw_values]

    async def mset(self, items: Mapping[IdType, ModelType], *, ttl: int | None = None) -> None:
        """Store every item. ``ttl`` applies to each id."""
        if not items:
            return
        mapping = {str(id): self.serializer.serialize(value) for id, value in items.items()}
        await self.storage.mset(self.key, mapping, ttl=ttl)
