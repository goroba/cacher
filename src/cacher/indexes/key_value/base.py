"""Shared key-value index attributes."""

from __future__ import annotations

from collections.abc import Hashable

from cacher.indexes.base import Index
from cacher.serializers.serializer import Serializer
from cacher.storage.key_value.async_storage import AsyncKeyValueStorage
from cacher.storage.key_value.storage import KeyValueStorage


class KeyValueBase[ClientType, IdType: Hashable, ModelType, StorageType](Index):
    """Identifier, model, serializer, storage key, and storage for a key-value index.

    ``ModelType`` is unconstrained: a builtin such as ``int`` or any class.
    ``key`` names that model in storage. For a hash storage it is the hash name.
    ``storage`` is the key-value storage instance. Fields are stored as ``str``.
    Each call receives the storage client.
    """

    identifier: type[IdType]
    model: type[ModelType]
    serializer: Serializer[ModelType, StorageType]
    storage: (
        KeyValueStorage[ClientType, str, StorageType]
        | AsyncKeyValueStorage[ClientType, str, StorageType]
    )
