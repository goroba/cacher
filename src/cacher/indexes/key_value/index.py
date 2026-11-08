"""Synchronous key-value index."""

from collections.abc import Hashable, Mapping, Sequence

from cacher.indexes.key_value.base import KeyValueBase
from cacher.storage.key_value.storage import KeyValueStorage


class KeyValueIndex[ClientType, IdType: Hashable, ModelType, StorageType](
    KeyValueBase[ClientType, IdType, ModelType, StorageType]
):
    """Sync key-value index: model binding, storage key, and the storage that persists it.

    Reads deserialize and writes serialize. The identifier is stored as ``str(id)``.
    """

    storage: KeyValueStorage[ClientType, str, StorageType]

    def get(self, client: ClientType, id: IdType) -> ModelType | None:
        """Return the cached model, or ``None`` when the id is missing."""
        raw = self.storage.get(client, self.key, str(id))
        if raw is None:
            return None
        return self.serializer.deserialize(raw)

    def set(
        self, client: ClientType, id: IdType, value: ModelType, *, ttl: int | None = None
    ) -> None:
        """Store ``value`` under ``id``."""
        self.storage.set(client, self.key, str(id), self.serializer.serialize(value), ttl=ttl)

    def delete(self, client: ClientType, id: IdType) -> None:
        """Remove ``id``. A missing id is not an error."""
        self.storage.delete(client, self.key, str(id))

    def exists(self, client: ClientType, id: IdType) -> bool:
        """Return whether ``id`` is present."""
        return self.storage.exists(client, self.key, str(id))

    def mget(self, client: ClientType, ids: Sequence[IdType]) -> list[ModelType | None]:
        """Return models in input order. Missing ids are ``None``."""
        if not ids:
            return []
        raw_values = self.storage.mget(client, self.key, [str(id) for id in ids])
        return [None if raw is None else self.serializer.deserialize(raw) for raw in raw_values]

    def mset(
        self, client: ClientType, items: Mapping[IdType, ModelType], *, ttl: int | None = None
    ) -> None:
        """Store every item. ``ttl`` applies to each id."""
        if not items:
            return
        mapping = {str(id): self.serializer.serialize(value) for id, value in items.items()}
        self.storage.mset(client, self.key, mapping, ttl=ttl)
