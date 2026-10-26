"""Synchronous set index."""

from collections.abc import Hashable, Sequence

from cacher.indexes.base import _sync_indexes
from cacher.indexes.sets.base_index import SetBase
from cacher.storage.sets.storage import SetStorage


class SetIndex[MemberType, StorageType: Hashable](SetBase[MemberType, StorageType]):
    """Sync set index: member binding, storage key, and the storage that persists it.

    Writes serialize the member. ``contains`` serializes the lookup value.
    """

    storage: SetStorage[StorageType]
    _registry = _sync_indexes

    def add(self, member: MemberType) -> None:
        """Add ``member``. A member that is already present is not an error."""
        self.storage.add(self.key, self.serializer.serialize(member))

    def madd(self, members: Sequence[MemberType]) -> None:
        """Add every member."""
        if not members:
            return
        self.storage.madd(self.key, [self.serializer.serialize(member) for member in members])

    def remove(self, member: MemberType) -> None:
        """Remove ``member``. A missing member is not an error."""
        self.storage.remove(self.key, self.serializer.serialize(member))

    def mremove(self, members: Sequence[MemberType]) -> None:
        """Remove every member. Missing members are not an error."""
        if not members:
            return
        self.storage.mremove(self.key, [self.serializer.serialize(member) for member in members])

    def contains(self, member: MemberType) -> bool:
        """Return whether ``member`` is in the set."""
        return self.storage.contains(self.key, self.serializer.serialize(member))
