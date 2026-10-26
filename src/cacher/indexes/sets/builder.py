"""Build a registered set index from its parts and check that those parts agree."""

from collections.abc import Hashable
from typing import Any, Protocol, cast

from cacher.engines.sets.async_engine import AsyncSetEngine
from cacher.engines.sets.engine import SetEngine
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


class _SyncSetIndexFactory[
    MemberType,
    StorageType: Hashable,
    EngineType: SetEngine[StorageType],
](Protocol):
    """Sync set index class. Call it with an engine instance."""

    member: type[MemberType]
    serializer: Serializer[MemberType, StorageType]
    key: str
    engine: type[EngineType]

    def __call__(self, engine: EngineType) -> SetIndex[MemberType, StorageType]: ...


class _AsyncSetIndexFactory[
    MemberType,
    StorageType: Hashable,
    EngineType: AsyncSetEngine[StorageType],
](Protocol):
    """Async set index class. Call it with an engine instance."""

    member: type[MemberType]
    serializer: Serializer[MemberType, StorageType]
    key: str
    engine: type[EngineType]

    def __call__(self, engine: EngineType) -> AsyncSetIndex[MemberType, StorageType]: ...


def build_set_index[
    MemberType,
    StorageType: Hashable,
    EngineType: SetEngine[StorageType],
](
    key: str,
    *,
    member_type: type[MemberType],
    serializer: type[Serializer[MemberType, StorageType]],
    engine: type[EngineType],
) -> _SyncSetIndexFactory[MemberType, StorageType, EngineType]:
    """Register a sync set index whose member, serializer, and engine types agree.

    The serializer is constructed here. Call the result with an engine instance;
    the engine's own constructor arguments stay with the caller.
    """
    return cast(
        _SyncSetIndexFactory[MemberType, StorageType, EngineType],
        _build(
            key,
            member_type=member_type,
            serializer=serializer,
            engine=engine,
            base=SetIndex,
            protocol=SetEngine,
            other=AsyncSetEngine,
        ),
    )


def build_async_set_index[
    MemberType,
    StorageType: Hashable,
    EngineType: AsyncSetEngine[StorageType],
](
    key: str,
    *,
    member_type: type[MemberType],
    serializer: type[Serializer[MemberType, StorageType]],
    engine: type[EngineType],
) -> _AsyncSetIndexFactory[MemberType, StorageType, EngineType]:
    """Register an async set index whose member, serializer, and engine types agree.

    The serializer is constructed here. Call the result with an engine instance;
    the engine's own constructor arguments stay with the caller.
    """
    return cast(
        _AsyncSetIndexFactory[MemberType, StorageType, EngineType],
        _build(
            key,
            member_type=member_type,
            serializer=serializer,
            engine=engine,
            base=AsyncSetIndex,
            protocol=AsyncSetEngine,
            other=SetEngine,
        ),
    )


def _build(
    key: str,
    *,
    member_type: Any,
    serializer: Any,
    engine: Any,
    base: type[SetIndex[Any, Any]] | type[AsyncSetIndex[Any, Any]],
    protocol: type[SetEngine[Any]] | type[AsyncSetEngine[Any]],
    other: type[SetEngine[Any]] | type[AsyncSetEngine[Any]],
) -> type:
    check_key(key)
    value_type, serializer_storage = serializer_types(key, serializer)
    check_value_type(key, member_type, value_type, label="member type")
    engine_storage = _engine_storage(key, engine, protocol, other)
    check_storage_type(key, serializer_storage, engine_storage, engine)
    serializer_instance = construct_serializer(key, serializer, member_type)
    return index_class(
        key,
        serializer_instance=serializer_instance,
        engine=engine,
        base=base,
        module=__name__,
        attributes={"member": member_type},
    )


def _engine_storage(
    key: str,
    engine: Any,
    protocol: type,
    other: type,
) -> Any:
    if not isinstance(engine, type):
        raise TypeError(f"index {key!r}: engine must be a class, got {type(engine).__name__}")
    args = protocol_args(engine, protocol)
    if args is None or len(args) != 1:
        if protocol_args(engine, other) is not None:
            if protocol is SetEngine:
                raise TypeError(
                    f"index {key!r}: {engine.__name__} is asynchronous; "
                    "build_set_index requires SetEngine"
                )
            raise TypeError(
                f"index {key!r}: {engine.__name__} is synchronous; "
                "build_async_set_index requires AsyncSetEngine"
            )
        raise TypeError(
            f"index {key!r}: {engine.__name__} does not declare {protocol.__name__}[MemberType]"
        )
    return args[0]
