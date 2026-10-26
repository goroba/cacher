"""Asynchronous index."""

from collections.abc import Hashable, Mapping, Sequence

from cacher.engines.async_engine import AsyncEngine
from cacher.indexes.base_index import BaseIndex, _async_indexes


class AsyncIndex[IdType: Hashable, ModelType, StorageType](BaseIndex[IdType, ModelType, StorageType]):
    """Async index: model binding, storage key, and the engine that persists it.

    Reads deserialize and writes serialize. The identifier is stored as ``str(id)``.
    """

    engine: AsyncEngine[str, StorageType]
    _registry = _async_indexes

    async def get(self, id: IdType) -> ModelType | None:
        """Return the cached model, or ``None`` when the id is missing."""
        raw = await self.engine.get(self.key, str(id))
        if raw is None:
            return None
        return self.serializer.deserialize(raw)

    async def set(self, id: IdType, value: ModelType, *, ttl: int | None = None) -> None:
        """Store ``value`` under ``id``."""
        await self.engine.set(self.key, str(id), self.serializer.serialize(value), ttl=ttl)

    async def delete(self, id: IdType) -> None:
        """Remove ``id``. A missing id is not an error."""
        await self.engine.delete(self.key, str(id))

    async def exists(self, id: IdType) -> bool:
        """Return whether ``id`` is present."""
        return await self.engine.exists(self.key, str(id))

    async def mget(self, ids: Sequence[IdType]) -> list[ModelType | None]:
        """Return models in input order. Missing ids are ``None``."""
        if not ids:
            return []
        raw_values = await self.engine.mget(self.key, [str(id) for id in ids])
        return [None if raw is None else self.serializer.deserialize(raw) for raw in raw_values]

    async def mset(self, items: Mapping[IdType, ModelType], *, ttl: int | None = None) -> None:
        """Store every item. ``ttl`` applies to each id."""
        if not items:
            return
        mapping = {str(id): self.serializer.serialize(value) for id, value in items.items()}
        await self.engine.mset(self.key, mapping, ttl=ttl)
