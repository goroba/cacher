"""Build a registered key-value index from its parts and check that those parts agree."""

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
from cacher.indexes.key_value.async_index import AsyncKeyValueIndex
from cacher.indexes.key_value.index import KeyValueIndex
from cacher.serializers.serializer import Serializer
from cacher.storage.key_value.async_storage import AsyncKeyValueStorage
from cacher.storage.key_value.storage import KeyValueStorage


def build_key_value_index[
    ClientType,
    IdType: Hashable,
    ModelType,
    StorageType,
    Storage: KeyValueStorage[ClientType, str, StorageType],
](
    key: str,
    *,
    id_type: type[IdType],
    model_type: type[ModelType],
    serializer: Serializer[ModelType, StorageType],
    storage: Storage,
) -> KeyValueIndex[ClientType, IdType, ModelType, StorageType]:
    """Register a sync key-value index whose id, model, serializer, and storage types agree.

    ``serializer`` and ``storage`` are instances. The returned index is registered
    and ready to use. Pass the storage client to each index method.
    """
    return cast(
        KeyValueIndex[ClientType, IdType, ModelType, StorageType],
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
    ClientType,
    IdType: Hashable,
    ModelType,
    StorageType,
    Storage: AsyncKeyValueStorage[ClientType, str, StorageType],
](
    key: str,
    *,
    id_type: type[IdType],
    model_type: type[ModelType],
    serializer: Serializer[ModelType, StorageType],
    storage: Storage,
) -> AsyncKeyValueIndex[ClientType, IdType, ModelType, StorageType]:
    """Register an async key-value index whose id, model, serializer, and storage types agree.

    ``serializer`` and ``storage`` are instances. The returned index is registered
    and ready to use. Pass the storage client to each index method.
    """
    return cast(
        AsyncKeyValueIndex[ClientType, IdType, ModelType, StorageType],
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
    base: type[KeyValueIndex[Any, Any, Any, Any]] | type[AsyncKeyValueIndex[Any, Any, Any, Any]],
    protocol: type[KeyValueStorage[Any, Any, Any]] | type[AsyncKeyValueStorage[Any, Any, Any]],
    other: type[KeyValueStorage[Any, Any, Any]] | type[AsyncKeyValueStorage[Any, Any, Any]],
) -> Any:
    check_key(key)
    _check_id_type(key, id_type)
    serializer_cls = instance_class(key, serializer, label="serializer")
    value_type, serializer_storage = serializer_types(key, serializer_cls)
    check_value_type(key, model_type, value_type, label="model type")
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
        attributes={"identifier": id_type, "model": model_type, "client_type": client_type},
    )


def _check_id_type(key: str, id_type: Any) -> None:
    if isinstance(id_type, type) and id_type.__hash__ is not None:
        return
    raise TypeError(f"index {key!r}: id type must be a hashable class, got {id_type!r}")


def _storage_type(
    key: str,
    storage: type,
    protocol: type,
    other: type,
) -> Any:
    args = protocol_args(storage, protocol)
    if args is None or len(args) != 3:
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
            f"{protocol.__name__}[ClientType, FieldType, StorageType]"
        )
    field_type, storage_type = args[1:]
    if field_type is not str:
        raise TypeError(
            f"index {key!r}: {storage.__name__} field type must be str, got {field_type!r}"
        )
    return storage_type
