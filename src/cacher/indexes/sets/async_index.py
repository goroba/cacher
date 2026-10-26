"""Asynchronous set index."""

from collections.abc import Hashable, Sequence

from cacher.engines.sets.async_engine import AsyncSetEngine
from cacher.indexes.sets.base_index import _SetBase, _async_indexes


class AsyncSetIndex[MemberType, StorageType: Hashable](_SetBase[MemberType, StorageType]):
    """Async set index: member binding, storage key, and the engine that persists it.

    Writes serialize the member. ``contains`` serializes the lookup value.
    """

    engine: AsyncSetEngine[StorageType]
    _registry = _async_indexes

    async def add(self, member: MemberType) -> None:
        """Add ``member``. A member that is already present is not an error."""
        await self.engine.add(self.key, self.serializer.serialize(member))

    async def madd(self, members: Sequence[MemberType]) -> None:
        """Add every member."""
        if not members:
            return
        serialized = [self.serializer.serialize(member) for member in members]
        await self.engine.madd(self.key, serialized)

    async def remove(self, member: MemberType) -> None:
        """Remove ``member``. A missing member is not an error."""
        await self.engine.remove(self.key, self.serializer.serialize(member))

    async def mremove(self, members: Sequence[MemberType]) -> None:
        """Remove every member. Missing members are not an error."""
        if not members:
            return
        serialized = [self.serializer.serialize(member) for member in members]
        await self.engine.mremove(self.key, serialized)

    async def contains(self, member: MemberType) -> bool:
        """Return whether ``member`` is in the set."""
        return await self.engine.contains(self.key, self.serializer.serialize(member))
