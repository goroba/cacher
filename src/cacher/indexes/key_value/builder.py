"""Build a registered key-value index from its parts and check that those parts agree."""

from collections.abc import Hashable
from typing import Any, Protocol, cast

from cacher.engines.key_value.async_engine import AsyncKeyValueEngine
from cacher.engines.key_value.engine import KeyValueEngine
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


class _SyncIndexFactory[
    IdType: Hashable,
    ModelType,
    StorageType,
    EngineType: KeyValueEngine[str, StorageType],
](Protocol):
    """Sync key-value index class. Call it with an engine instance."""

    identifier: type[IdType]
    model: type[ModelType]
    serializer: Serializer[ModelType, StorageType]
    key: str
    engine: type[EngineType]

    def __call__(self, engine: EngineType) -> KeyValueIndex[IdType, ModelType, StorageType]: ...


class _AsyncIndexFactory[
    IdType: Hashable,
    ModelType,
    StorageType,
    EngineType: AsyncKeyValueEngine[str, StorageType],
](Protocol):
    """Async key-value index class. Call it with an engine instance."""

    identifier: type[IdType]
    model: type[ModelType]
    serializer: Serializer[ModelType, StorageType]
    key: str
    engine: type[EngineType]

    def __call__(
        self, engine: EngineType
    ) -> AsyncKeyValueIndex[IdType, ModelType, StorageType]: ...


def build_key_value_index[
    IdType: Hashable,
    ModelType,
    StorageType,
    EngineType: KeyValueEngine[str, StorageType],
](
    key: str,
    *,
    id_type: type[IdType],
    model_type: type[ModelType],
    serializer: type[Serializer[ModelType, StorageType]],
    engine: type[EngineType],
) -> _SyncIndexFactory[IdType, ModelType, StorageType, EngineType]:
    """Register a sync key-value index whose id, model, serializer, and engine types agree.

    The serializer is constructed here. Call the result with an engine instance;
    the engine's own constructor arguments stay with the caller.
    """
    return cast(
        _SyncIndexFactory[IdType, ModelType, StorageType, EngineType],
        _build(
            key,
            id_type=id_type,
            model_type=model_type,
            serializer=serializer,
            engine=engine,
            base=KeyValueIndex,
            protocol=KeyValueEngine,
            other=AsyncKeyValueEngine,
        ),
    )


def build_async_key_value_index[
    IdType: Hashable,
    ModelType,
    StorageType,
    EngineType: AsyncKeyValueEngine[str, StorageType],
](
    key: str,
    *,
    id_type: type[IdType],
    model_type: type[ModelType],
    serializer: type[Serializer[ModelType, StorageType]],
    engine: type[EngineType],
) -> _AsyncIndexFactory[IdType, ModelType, StorageType, EngineType]:
    """Register an async key-value index whose id, model, serializer, and engine types agree.

    The serializer is constructed here. Call the result with an engine instance;
    the engine's own constructor arguments stay with the caller.
    """
    return cast(
        _AsyncIndexFactory[IdType, ModelType, StorageType, EngineType],
        _build(
            key,
            id_type=id_type,
            model_type=model_type,
            serializer=serializer,
            engine=engine,
            base=AsyncKeyValueIndex,
            protocol=AsyncKeyValueEngine,
            other=KeyValueEngine,
        ),
    )


def _build(
    key: str,
    *,
    id_type: Any,
    model_type: Any,
    serializer: Any,
    engine: Any,
    base: type[KeyValueIndex[Any, Any, Any]] | type[AsyncKeyValueIndex[Any, Any, Any]],
    protocol: type[KeyValueEngine[Any, Any]] | type[AsyncKeyValueEngine[Any, Any]],
    other: type[KeyValueEngine[Any, Any]] | type[AsyncKeyValueEngine[Any, Any]],
) -> type:
    check_key(key)
    _check_id_type(key, id_type)
    value_type, serializer_storage = serializer_types(key, serializer)
    check_value_type(key, model_type, value_type, label="model type")
    engine_storage = _engine_storage(key, engine, protocol, other)
    check_storage_type(key, serializer_storage, engine_storage, engine)
    serializer_instance = construct_serializer(key, serializer, model_type)
    return index_class(
        key,
        serializer_instance=serializer_instance,
        engine=engine,
        base=base,
        module=__name__,
        attributes={"identifier": id_type, "model": model_type},
    )


def _check_id_type(key: str, id_type: Any) -> None:
    if isinstance(id_type, type) and id_type.__hash__ is not None:
        return
    raise TypeError(f"index {key!r}: id type must be a hashable class, got {id_type!r}")


def _engine_storage(
    key: str,
    engine: Any,
    protocol: type,
    other: type,
) -> Any:
    if not isinstance(engine, type):
        raise TypeError(f"index {key!r}: engine must be a class, got {type(engine).__name__}")
    args = protocol_args(engine, protocol)
    if args is None or len(args) != 2:
        if protocol_args(engine, other) is not None:
            if protocol is KeyValueEngine:
                raise TypeError(
                    f"index {key!r}: {engine.__name__} is asynchronous; "
                    "build_key_value_index requires KeyValueEngine"
                )
            raise TypeError(
                f"index {key!r}: {engine.__name__} is synchronous; "
                "build_async_key_value_index requires AsyncKeyValueEngine"
            )
        raise TypeError(
            f"index {key!r}: {engine.__name__} does not declare "
            f"{protocol.__name__}[FieldType, StorageType]"
        )
    field_type, storage_type = args
    if field_type is not str:
        raise TypeError(
            f"index {key!r}: {engine.__name__} field type must be str, got {field_type!r}"
        )
    return storage_type
