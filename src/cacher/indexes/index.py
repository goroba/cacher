"""Synchronous index."""

from collections.abc import Hashable, Mapping, Sequence

from cacher.engines.engine import Engine
from cacher.indexes.base_index import BaseIndex, _sync_indexes


class Index[IdType: Hashable, ModelType, StorageType](BaseIndex[IdType, ModelType, StorageType]):
    """Sync index: model binding, storage key, and the engine that persists it.

    Reads deserialize and writes serialize. The identifier is stored as ``str(id)``.
    """

    engine: Engine[str, StorageType]
    _registry = _sync_indexes

    def get(self, id: IdType) -> ModelType | None:
        """Return the cached model, or ``None`` when the id is missing."""
        raw = self.engine.get(self.key, str(id))
        if raw is None:
            return None
        return self.serializer.deserialize(raw)

    def set(self, id: IdType, value: ModelType, *, ttl: int | None = None) -> None:
        """Store ``value`` under ``id``."""
        self.engine.set(self.key, str(id), self.serializer.serialize(value), ttl=ttl)

    def delete(self, id: IdType) -> None:
        """Remove ``id``. A missing id is not an error."""
        self.engine.delete(self.key, str(id))

    def exists(self, id: IdType) -> bool:
        """Return whether ``id`` is present."""
        return self.engine.exists(self.key, str(id))

    def mget(self, ids: Sequence[IdType]) -> list[ModelType | None]:
        """Return models in input order. Missing ids are ``None``."""
        if not ids:
            return []
        raw_values = self.engine.mget(self.key, [str(id) for id in ids])
        return [None if raw is None else self.serializer.deserialize(raw) for raw in raw_values]

    def mset(self, items: Mapping[IdType, ModelType], *, ttl: int | None = None) -> None:
        """Store every item. ``ttl`` applies to each id."""
        if not items:
            return
        mapping = {str(id): self.serializer.serialize(value) for id, value in items.items()}
        self.engine.mset(self.key, mapping, ttl=ttl)
