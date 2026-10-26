"""Shared set index attributes."""

from __future__ import annotations

from collections.abc import Hashable

from cacher.indexes.base import Index
from cacher.serializers.serializer import Serializer
from cacher.storage.sets.async_storage import AsyncSetStorage
from cacher.storage.sets.storage import SetStorage


class SetBase[MemberType, StorageType: Hashable](Index):
    """Member, serializer, storage key, and storage for a set index.

    ``key`` is the set name. ``storage`` stores serialized members.
    """

    member: type[MemberType]
    serializer: Serializer[MemberType, StorageType]
    storage: SetStorage[StorageType] | AsyncSetStorage[StorageType]
