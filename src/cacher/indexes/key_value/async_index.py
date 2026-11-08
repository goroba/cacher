"""Asynchronous key-value index."""

from collections.abc import Hashable, Mapping, Sequence

from cacher.indexes.key_value.base import KeyValueBase
from cacher.storage.key_value.async_storage import AsyncKeyValueStorage


class AsyncKeyValueIndex[ClientType, IdType: Hashable, ModelType, StorageType](
    KeyValueBase[ClientType, IdType, ModelType, StorageType]
):
    """Async key-value index: model binding, storage key, and the storage that persists it.

    Reads deserialize and writes serialize. The identifier is stored as ``str(id)``.
    """

    storage: AsyncKeyValueStorage[ClientType, str, StorageType]

    async def get(self, client: ClientType, id: IdType) -> ModelType | None:
        """Return the cached model, or ``None`` when the id is missing."""
        raw = await self.storage.get(client, self.key, str(id))
        if raw is None:
            return None
        return self.serializer.deserialize(raw)

    async def set(
        self, client: ClientType, id: IdType, value: ModelType, *, ttl: int | None = None
    ) -> None:
        """Store ``value`` under ``id``."""
        await self.storage.set(client, self.key, str(id), self.serializer.serialize(value), ttl=ttl)

    async def delete(self, client: ClientType, id: IdType) -> None:
        """Remove ``id``. A missing id is not an error."""
        await self.storage.delete(client, self.key, str(id))

    async def exists(self, client: ClientType, id: IdType) -> bool:
        """Return whether ``id`` is present."""
        return await self.storage.exists(client, self.key, str(id))

    async def mget(self, client: ClientType, ids: Sequence[IdType]) -> list[ModelType | None]:
        """Return models in input order. Missing ids are ``None``."""
        if not ids:
            return []
        raw_values = await self.storage.mget(client, self.key, [str(id) for id in ids])
        return [None if raw is None else self.serializer.deserialize(raw) for raw in raw_values]

    async def mset(
        self, client: ClientType, items: Mapping[IdType, ModelType], *, ttl: int | None = None
    ) -> None:
        """Store every item. ``ttl`` applies to each id."""
        if not items:
            return
        mapping = {str(id): self.serializer.serialize(value) for id, value in items.items()}
        await self.storage.mset(client, self.key, mapping, ttl=ttl)
