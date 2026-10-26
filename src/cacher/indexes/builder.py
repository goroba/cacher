"""Build a registered index from its parts and check that those parts agree."""

import inspect
import types
from collections.abc import Hashable
from typing import Any, Generic, Protocol, TypeVar, cast, get_args, get_origin

from cacher.engines.async_engine import AsyncEngine
from cacher.engines.engine import Engine
from cacher.indexes.async_index import AsyncIndex
from cacher.indexes.index import Index
from cacher.serializers.serializer import Serializer


class _SyncIndexFactory[
    IdType: Hashable,
    ModelType,
    StorageType,
    EngineType: Engine[str, StorageType],
](Protocol):
    """Sync index class. Call it with an engine instance."""

    identifier: type[IdType]
    model: type[ModelType]
    serializer: Serializer[ModelType, StorageType]
    key: str
    engine: type[EngineType]

    def __call__(self, engine: EngineType) -> Index[IdType, ModelType, StorageType]: ...


class _AsyncIndexFactory[
    IdType: Hashable,
    ModelType,
    StorageType,
    EngineType: AsyncEngine[str, StorageType],
](Protocol):
    """Async index class. Call it with an engine instance."""

    identifier: type[IdType]
    model: type[ModelType]
    serializer: Serializer[ModelType, StorageType]
    key: str
    engine: type[EngineType]

    def __call__(
        self, engine: EngineType
    ) -> AsyncIndex[IdType, ModelType, StorageType]: ...


def build_index[IdType: Hashable, ModelType, StorageType, EngineType: Engine[str, StorageType]](
    key: str,
    *,
    id_type: type[IdType],
    model_type: type[ModelType],
    serializer: type[Serializer[ModelType, StorageType]],
    engine: type[EngineType],
) -> _SyncIndexFactory[IdType, ModelType, StorageType, EngineType]:
    """Register a sync index whose id, model, serializer, and engine types agree.

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
            base=Index,
            protocol=Engine,
            other=AsyncEngine,
        ),
    )


def build_async_index[
    IdType: Hashable,
    ModelType,
    StorageType,
    EngineType: AsyncEngine[str, StorageType],
](
    key: str,
    *,
    id_type: type[IdType],
    model_type: type[ModelType],
    serializer: type[Serializer[ModelType, StorageType]],
    engine: type[EngineType],
) -> _AsyncIndexFactory[IdType, ModelType, StorageType, EngineType]:
    """Register an async index whose id, model, serializer, and engine types agree.

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
            base=AsyncIndex,
            protocol=AsyncEngine,
            other=Engine,
        ),
    )


def _build(
    key: str,
    *,
    id_type: Any,
    model_type: Any,
    serializer: Any,
    engine: Any,
    base: type[Index[Any, Any, Any]] | type[AsyncIndex[Any, Any, Any]],
    protocol: type[Engine[Any, Any]] | type[AsyncEngine[Any, Any]],
    other: type[Engine[Any, Any]] | type[AsyncEngine[Any, Any]],
) -> type:
    if not isinstance(key, str) or key == "":
        raise TypeError(f"index key must be a non-empty str, got {key!r}")
    _check_id_type(key, id_type)
    value_type, serializer_storage = _serializer_types(key, serializer)
    _check_model_type(key, model_type, value_type)
    _, engine_storage = _engine_types(key, engine, protocol, other)
    if serializer_storage != engine_storage:
        raise TypeError(
            f"index {key!r}: serializer storage type {serializer_storage!r} "
            f"does not match {engine.__name__} storage type {engine_storage!r}"
        )
    serializer_instance = _construct_serializer(key, serializer, model_type)
    return _index_class(
        key,
        id_type=id_type,
        model_type=model_type,
        serializer_instance=serializer_instance,
        engine=engine,
        base=base,
    )


def _check_id_type(key: str, id_type: Any) -> None:
    if isinstance(id_type, type) and id_type.__hash__ is not None:
        return
    raise TypeError(f"index {key!r}: id type must be a hashable class, got {id_type!r}")


def _serializer_types(key: str, serializer: Any) -> tuple[Any, Any]:
    if not isinstance(serializer, type):
        raise TypeError(
            f"index {key!r}: serializer must be a class, got {type(serializer).__name__}"
        )
    args = _protocol_args(serializer, Serializer)
    if args is None or len(args) != 2:
        raise TypeError(
            f"index {key!r}: {serializer.__name__} does not declare "
            "Serializer[ValueType, StorageType]"
        )
    return args


def _engine_types(
    key: str,
    engine: Any,
    protocol: type,
    other: type,
) -> tuple[Any, Any]:
    if not isinstance(engine, type):
        raise TypeError(f"index {key!r}: engine must be a class, got {type(engine).__name__}")
    args = _protocol_args(engine, protocol)
    if args is None or len(args) != 2:
        if _protocol_args(engine, other) is not None:
            if protocol is Engine:
                raise TypeError(
                    f"index {key!r}: {engine.__name__} is asynchronous; "
                    "build_index requires Engine"
                )
            raise TypeError(
                f"index {key!r}: {engine.__name__} is synchronous; "
                "build_async_index requires AsyncEngine"
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
    return field_type, storage_type


def _check_model_type(key: str, model_type: Any, value_type: Any) -> None:
    if _model_matches(value_type, model_type):
        return
    raise TypeError(
        f"index {key!r}: model type {model_type!r} does not match "
        f"serializer value type {value_type!r}"
    )


def _model_matches(value_type: Any, model_type: Any) -> bool:
    if not isinstance(value_type, TypeVar):
        return model_type == value_type
    constraints = value_type.__constraints__
    if constraints:
        return any(
            model_type == constraint or _is_subclass(model_type, constraint)
            for constraint in constraints
        )
    bound = value_type.__bound__
    if bound is None:
        return isinstance(model_type, type)
    return _is_subclass(model_type, bound)


def _is_subclass(model_type: Any, parent: Any) -> bool:
    if not isinstance(model_type, type):
        return False
    origin = get_origin(parent)
    parent_type = origin if isinstance(origin, type) else parent
    if not isinstance(parent_type, type):
        return False
    try:
        return issubclass(model_type, parent_type)
    except TypeError:
        return False


def _protocol_args(cls: Any, protocol: type) -> tuple[Any, ...] | None:
    return _walk_protocol_args(cls, protocol, {}, ())


def _walk_protocol_args(
    cls: Any,
    protocol: type,
    subst: dict[Any, Any],
    stack: tuple[type, ...],
) -> tuple[Any, ...] | None:
    if not isinstance(cls, type) or cls in stack or cls in {object, Protocol, Generic}:
        return None
    stack = (*stack, cls)
    for base in types.get_original_bases(cls):
        origin = get_origin(base)
        if origin is None:
            found = _walk_protocol_args(base, protocol, subst, stack)
            if found is not None:
                return found
            continue
        if origin is protocol:
            return tuple(_substitute(arg, subst) for arg in get_args(base))
        if not isinstance(origin, type):
            continue
        args = get_args(base)
        params = getattr(origin, "__type_params__", ())
        local = dict(subst)
        if len(params) == len(args):
            for param, arg in zip(params, args, strict=True):
                local[param] = _substitute(arg, subst)
        found = _walk_protocol_args(origin, protocol, local, stack)
        if found is not None:
            return found
    return None


def _substitute(tp: Any, subst: dict[Any, Any]) -> Any:
    if isinstance(tp, TypeVar):
        return subst.get(tp, tp)
    origin = get_origin(tp)
    if origin is None:
        return tp
    args = get_args(tp)
    substituted = tuple(_substitute(arg, subst) for arg in args)
    if substituted == args:
        return tp
    try:
        return origin[substituted]
    except TypeError:
        return tp


def _construct_serializer(key: str, serializer: type, model_type: Any) -> Any:
    required = _required_parameters(serializer)
    if not required:
        return serializer()
    if len(required) == 1 and required[0].kind is not inspect.Parameter.KEYWORD_ONLY:
        return serializer(model_type)
    raise TypeError(
        f"index {key!r}: {serializer.__name__} cannot be built from the model type alone"
    )


def _required_parameters(cls: type) -> list[inspect.Parameter]:
    try:
        signature = inspect.signature(cls.__init__)
    except (TypeError, ValueError):
        return []
    parameters = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }
    ]
    if parameters and parameters[0].name == "self":
        parameters = parameters[1:]
    return [parameter for parameter in parameters if parameter.default is inspect.Parameter.empty]


def _index_class(
    key: str,
    *,
    id_type: Any,
    model_type: Any,
    serializer_instance: Any,
    engine: type,
    base: type,
) -> type:
    suffix = "".join(char if char.isalnum() else "_" for char in key)

    def __init__(self: Any, engine_instance: object) -> None:
        if not isinstance(engine_instance, engine):
            raise TypeError(
                f"expected {engine.__name__}, got {type(engine_instance).__name__}"
            )
        self.engine = engine_instance

    return type(
        f"{base.__name__}_{suffix}",
        (base,),
        {
            "__module__": __name__,
            "identifier": id_type,
            "model": model_type,
            "serializer": serializer_instance,
            "key": key,
            "engine": engine,
            "__init__": __init__,
        },
    )
