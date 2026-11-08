"""Build a registered set index from its parts and check that those parts agree."""

from collections.abc import Hashable
from typing import Any, cast

from cacher.indexes._builder import (
    check_key,
    check_storage_type,
    check_value_type,
    index_class,
    instance_class,
    protocol_args,
    serializer_types,
    storage_client_type,
)
from cacher.indexes.sets.async_index import AsyncSetIndex
from cacher.indexes.sets.index import SetIndex
from cacher.serializers.serializer import Serializer
from cacher.storage.sets.async_storage import AsyncSetStorage
from cacher.storage.sets.storage import SetStorage


def build_set_index[
    ClientType,
    MemberType,
    StorageType: Hashable,
    Storage: SetStorage[ClientType, StorageType],
](
    key: str,
    *,
    member_type: type[MemberType],
    serializer: Serializer[MemberType, StorageType],
    storage: Storage,
) -> SetIndex[ClientType, MemberType, StorageType]:
    """Register a sync set index whose member, serializer, and storage types agree.

    ``serializer`` and ``storage`` are instances. The returned index is registered
    and ready to use. Pass the storage client to each index method.
    """
    return cast(
        SetIndex[ClientType, MemberType, StorageType],
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
    ClientType,
    MemberType,
    StorageType: Hashable,
    Storage: AsyncSetStorage[ClientType, StorageType],
](
    key: str,
    *,
    member_type: type[MemberType],
    serializer: Serializer[MemberType, StorageType],
    storage: Storage,
) -> AsyncSetIndex[ClientType, MemberType, StorageType]:
    """Register an async set index whose member, serializer, and storage types agree.

    ``serializer`` and ``storage`` are instances. The returned index is registered
    and ready to use. Pass the storage client to each index method.
    """
    return cast(
        AsyncSetIndex[ClientType, MemberType, StorageType],
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
    base: type[SetIndex[Any, Any, Any]] | type[AsyncSetIndex[Any, Any, Any]],
    protocol: type[SetStorage[Any, Any]] | type[AsyncSetStorage[Any, Any]],
    other: type[SetStorage[Any, Any]] | type[AsyncSetStorage[Any, Any]],
) -> Any:
    check_key(key)
    serializer_cls = instance_class(key, serializer, label="serializer")
    value_type, serializer_storage = serializer_types(key, serializer_cls)
    check_value_type(key, member_type, value_type, label="member type")
    storage_cls = instance_class(key, storage, label="storage")
    storage_type = _storage_type(key, storage_cls, protocol, other)
    check_storage_type(key, serializer_storage, storage_type, storage_cls)
    client_type = storage_client_type(key, storage_cls, protocol)
    return index_class(
        key,
        serializer_instance=serializer,
        storage=storage,
        base=base,
        module=__name__,
        attributes={"member": member_type, "client_type": client_type},
    )


def _storage_type(
    key: str,
    storage: type,
    protocol: type,
    other: type,
) -> Any:
    args = protocol_args(storage, protocol)
    if args is None or len(args) != 2:
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
            f"index {key!r}: {storage.__name__} does not declare "
            f"{protocol.__name__}[ClientType, MemberType]"
        )
    return args[1]
