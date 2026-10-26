"""Build a registered key-value index from its parts and check that those parts agree."""

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
from cacher.indexes.key_value.async_index import AsyncKeyValueIndex
from cacher.indexes.key_value.index import KeyValueIndex
from cacher.serializers.serializer import Serializer
from cacher.storage.key_value.async_storage import AsyncKeyValueStorage
from cacher.storage.key_value.storage import KeyValueStorage


class _SyncIndexFactory[
    IdType: Hashable,
    ModelType,
    StorageType,
    Storage: KeyValueStorage[str, StorageType],
](Protocol):
    """Sync key-value index class. Call it with a storage instance."""

    identifier: type[IdType]
    model: type[ModelType]
    serializer: Serializer[ModelType, StorageType]
    key: str
    storage: type[Storage]

    def __call__(self, storage: Storage) -> KeyValueIndex[IdType, ModelType, StorageType]: ...


class _AsyncIndexFactory[
    IdType: Hashable,
    ModelType,
    StorageType,
    Storage: AsyncKeyValueStorage[str, StorageType],
](Protocol):
    """Async key-value index class. Call it with a storage instance."""

    identifier: type[IdType]
    model: type[ModelType]
    serializer: Serializer[ModelType, StorageType]
    key: str
    storage: type[Storage]

    def __call__(
        self, storage: Storage
    ) -> AsyncKeyValueIndex[IdType, ModelType, StorageType]: ...


def build_key_value_index[
    IdType: Hashable,
    ModelType,
    StorageType,
    Storage: KeyValueStorage[str, StorageType],
](
    key: str,
    *,
    id_type: type[IdType],
    model_type: type[ModelType],
    serializer: type[Serializer[ModelType, StorageType]],
    storage: type[Storage],
) -> _SyncIndexFactory[IdType, ModelType, StorageType, Storage]:
    """Register a sync key-value index whose id, model, serializer, and storage types agree.

    The serializer is constructed here. Call the result with a storage instance;
    the storage's own constructor arguments stay with the caller.
    """
    return cast(
        _SyncIndexFactory[IdType, ModelType, StorageType, Storage],
        _build(
            key,
            id_type=id_type,
            model_type=model_type,
            serializer=serializer,
            storage=storage,
            base=KeyValueIndex,
            protocol=KeyValueStorage,
            other=AsyncKeyValueStorage,
        ),
    )


def build_async_key_value_index[
    IdType: Hashable,
    ModelType,
    StorageType,
    Storage: AsyncKeyValueStorage[str, StorageType],
](
    key: str,
    *,
    id_type: type[IdType],
    model_type: type[ModelType],
    serializer: type[Serializer[ModelType, StorageType]],
    storage: type[Storage],
) -> _AsyncIndexFactory[IdType, ModelType, StorageType, Storage]:
    """Register an async key-value index whose id, model, serializer, and storage types agree.

    The serializer is constructed here. Call the result with a storage instance;
    the storage's own constructor arguments stay with the caller.
    """
    return cast(
        _AsyncIndexFactory[IdType, ModelType, StorageType, Storage],
        _build(
            key,
            id_type=id_type,
            model_type=model_type,
            serializer=serializer,
            storage=storage,
            base=AsyncKeyValueIndex,
            protocol=AsyncKeyValueStorage,
            other=KeyValueStorage,
        ),
    )


def _build(
    key: str,
    *,
    id_type: Any,
    model_type: Any,
    serializer: Any,
    storage: Any,
    base: type[KeyValueIndex[Any, Any, Any]] | type[AsyncKeyValueIndex[Any, Any, Any]],
    protocol: type[KeyValueStorage[Any, Any]] | type[AsyncKeyValueStorage[Any, Any]],
    other: type[KeyValueStorage[Any, Any]] | type[AsyncKeyValueStorage[Any, Any]],
) -> type:
    check_key(key)
    _check_id_type(key, id_type)
    value_type, serializer_storage = serializer_types(key, serializer)
    check_value_type(key, model_type, value_type, label="model type")
    storage_type = _storage_type(key, storage, protocol, other)
    check_storage_type(key, serializer_storage, storage_type, storage)
    serializer_instance = construct_serializer(key, serializer, model_type)
    return index_class(
        key,
        serializer_instance=serializer_instance,
        storage=storage,
        base=base,
        module=__name__,
        attributes={"identifier": id_type, "model": model_type},
    )


def _check_id_type(key: str, id_type: Any) -> None:
    if isinstance(id_type, type) and id_type.__hash__ is not None:
        return
    raise TypeError(f"index {key!r}: id type must be a hashable class, got {id_type!r}")


def _storage_type(
    key: str,
    storage: Any,
    protocol: type,
    other: type,
) -> Any:
    if not isinstance(storage, type):
        raise TypeError(f"index {key!r}: storage must be a class, got {type(storage).__name__}")
    args = protocol_args(storage, protocol)
    if args is None or len(args) != 2:
        if protocol_args(storage, other) is not None:
            if protocol is KeyValueStorage:
                raise TypeError(
                    f"index {key!r}: {storage.__name__} is asynchronous; "
                    "build_key_value_index requires KeyValueStorage"
                )
            raise TypeError(
                f"index {key!r}: {storage.__name__} is synchronous; "
                "build_async_key_value_index requires AsyncKeyValueStorage"
            )
        raise TypeError(
            f"index {key!r}: {storage.__name__} does not declare "
            f"{protocol.__name__}[FieldType, StorageType]"
        )
    field_type, storage_type = args
    if field_type is not str:
        raise TypeError(
            f"index {key!r}: {storage.__name__} field type must be str, got {field_type!r}"
        )
    return storage_type
