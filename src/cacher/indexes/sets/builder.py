"""Build a registered set index from its parts and check that those parts agree."""

from collections.abc import Hashable
from typing import Any, Protocol, cast

from cacher.indexes._builder import (
    check_key,
    check_storage_type,
    check_value_type,
    construct_serializer,
    index_class,
    protocol_args,
    serializer_types,
)
from cacher.indexes.sets.async_index import AsyncSetIndex
from cacher.indexes.sets.index import SetIndex
from cacher.serializers.serializer import Serializer
from cacher.storage.sets.async_storage import AsyncSetStorage
from cacher.storage.sets.storage import SetStorage


class _SyncSetIndexFactory[
    MemberType,
    StorageType: Hashable,
    Storage: SetStorage[StorageType],
](Protocol):
    """Sync set index class. Call it with a storage instance."""

    member: type[MemberType]
    serializer: Serializer[MemberType, StorageType]
    key: str
    storage: type[Storage]

    def __call__(self, storage: Storage) -> SetIndex[MemberType, StorageType]: ...


class _AsyncSetIndexFactory[
    MemberType,
    StorageType: Hashable,
    Storage: AsyncSetStorage[StorageType],
](Protocol):
    """Async set index class. Call it with a storage instance."""

    member: type[MemberType]
    serializer: Serializer[MemberType, StorageType]
    key: str
    storage: type[Storage]

    def __call__(self, storage: Storage) -> AsyncSetIndex[MemberType, StorageType]: ...


def build_set_index[
    MemberType,
    StorageType: Hashable,
    Storage: SetStorage[StorageType],
](
    key: str,
    *,
    member_type: type[MemberType],
    serializer: type[Serializer[MemberType, StorageType]],
    storage: type[Storage],
) -> _SyncSetIndexFactory[MemberType, StorageType, Storage]:
    """Register a sync set index whose member, serializer, and storage types agree.

    The serializer is constructed here. Call the result with a storage instance;
    the storage's own constructor arguments stay with the caller.
    """
    return cast(
        _SyncSetIndexFactory[MemberType, StorageType, Storage],
        _build(
            key,
            member_type=member_type,
            serializer=serializer,
            storage=storage,
            base=SetIndex,
            protocol=SetStorage,
            other=AsyncSetStorage,
        ),
    )


def build_async_set_index[
    MemberType,
    StorageType: Hashable,
    Storage: AsyncSetStorage[StorageType],
](
    key: str,
    *,
    member_type: type[MemberType],
    serializer: type[Serializer[MemberType, StorageType]],
    storage: type[Storage],
) -> _AsyncSetIndexFactory[MemberType, StorageType, Storage]:
    """Register an async set index whose member, serializer, and storage types agree.

    The serializer is constructed here. Call the result with a storage instance;
    the storage's own constructor arguments stay with the caller.
    """
    return cast(
        _AsyncSetIndexFactory[MemberType, StorageType, Storage],
        _build(
            key,
            member_type=member_type,
            serializer=serializer,
            storage=storage,
            base=AsyncSetIndex,
            protocol=AsyncSetStorage,
            other=SetStorage,
        ),
    )


def _build(
    key: str,
    *,
    member_type: Any,
    serializer: Any,
    storage: Any,
    base: type[SetIndex[Any, Any]] | type[AsyncSetIndex[Any, Any]],
    protocol: type[SetStorage[Any]] | type[AsyncSetStorage[Any]],
    other: type[SetStorage[Any]] | type[AsyncSetStorage[Any]],
) -> type:
    check_key(key)
    value_type, serializer_storage = serializer_types(key, serializer)
    check_value_type(key, member_type, value_type, label="member type")
    storage_type = _storage_type(key, storage, protocol, other)
    check_storage_type(key, serializer_storage, storage_type, storage)
    serializer_instance = construct_serializer(key, serializer, member_type)
    return index_class(
        key,
        serializer_instance=serializer_instance,
        storage=storage,
        base=base,
        module=__name__,
        attributes={"member": member_type},
    )


def _storage_type(
    key: str,
    storage: Any,
    protocol: type,
    other: type,
) -> Any:
    if not isinstance(storage, type):
        raise TypeError(f"index {key!r}: storage must be a class, got {type(storage).__name__}")
    args = protocol_args(storage, protocol)
    if args is None or len(args) != 1:
        if protocol_args(storage, other) is not None:
            if protocol is SetStorage:
                raise TypeError(
                    f"index {key!r}: {storage.__name__} is asynchronous; "
                    "build_set_index requires SetStorage"
                )
            raise TypeError(
                f"index {key!r}: {storage.__name__} is synchronous; "
                "build_async_set_index requires AsyncSetStorage"
            )
        raise TypeError(
            f"index {key!r}: {storage.__name__} does not declare {protocol.__name__}[MemberType]"
        )
    return args[0]
