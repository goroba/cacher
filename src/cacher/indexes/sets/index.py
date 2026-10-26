"""Synchronous set index."""

from collections.abc import Hashable, Sequence

from cacher.engines.sets.engine import SetEngine
from cacher.indexes.sets.base_index import _SetBase, _sync_indexes


class SetIndex[MemberType, StorageType: Hashable](_SetBase[MemberType, StorageType]):
    """Sync set index: member binding, storage key, and the engine that persists it.

    Writes serialize the member. ``contains`` serializes the lookup value.
    """

    engine: SetEngine[StorageType]
    _registry = _sync_indexes

    def add(self, member: MemberType) -> None:
        """Add ``member``. A member that is already present is not an error."""
        self.engine.add(self.key, self.serializer.serialize(member))

    def madd(self, members: Sequence[MemberType]) -> None:
        """Add every member."""
        if not members:
            return
        self.engine.madd(self.key, [self.serializer.serialize(member) for member in members])

    def remove(self, member: MemberType) -> None:
        """Remove ``member``. A missing member is not an error."""
        self.engine.remove(self.key, self.serializer.serialize(member))

    def mremove(self, members: Sequence[MemberType]) -> None:
        """Remove every member. Missing members are not an error."""
        if not members:
            return
        self.engine.mremove(self.key, [self.serializer.serialize(member) for member in members])

    def contains(self, member: MemberType) -> bool:
        """Return whether ``member`` is in the set."""
        return self.engine.contains(self.key, self.serializer.serialize(member))
