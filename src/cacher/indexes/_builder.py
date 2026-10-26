"""Shared checks for building a registered index."""

import inspect
import types
from typing import Any, Generic, Protocol, TypeVar, get_args, get_origin

from cacher.serializers.serializer import Serializer


def check_key(key: str) -> None:
    if not isinstance(key, str) or key == "":
        raise TypeError(f"index key must be a non-empty str, got {key!r}")


def serializer_types(key: str, serializer: Any) -> tuple[Any, Any]:
    if not isinstance(serializer, type):
        raise TypeError(
            f"index {key!r}: serializer must be a class, got {type(serializer).__name__}"
        )
    args = protocol_args(serializer, Serializer)
    if args is None or len(args) != 2:
        raise TypeError(
            f"index {key!r}: {serializer.__name__} does not declare "
            "Serializer[ValueType, StorageType]"
        )
    return args


def check_value_type(key: str, declared: Any, value_type: Any, *, label: str) -> None:
    if value_matches(value_type, declared):
        return
    raise TypeError(
        f"index {key!r}: {label} {declared!r} does not match "
        f"serializer value type {value_type!r}"
    )


def check_storage_type(key: str, serializer_storage: Any, engine_storage: Any, engine: Any) -> None:
    if serializer_storage != engine_storage:
        raise TypeError(
            f"index {key!r}: serializer storage type {serializer_storage!r} "
            f"does not match {engine.__name__} storage type {engine_storage!r}"
        )


def value_matches(value_type: Any, declared: Any) -> bool:
    if not isinstance(value_type, TypeVar):
        return declared == value_type
    constraints = value_type.__constraints__
    if constraints:
        return any(
            declared == constraint or _is_subclass(declared, constraint)
            for constraint in constraints
        )
    bound = value_type.__bound__
    if bound is None:
        return isinstance(declared, type)
    return _is_subclass(declared, bound)


def protocol_args(cls: Any, protocol: type) -> tuple[Any, ...] | None:
    return _walk_protocol_args(cls, protocol, {}, ())


def construct_serializer(key: str, serializer: type, value_type: Any) -> Any:
    required = _required_parameters(serializer)
    if not required:
        return serializer()
    if len(required) == 1 and required[0].kind is not inspect.Parameter.KEYWORD_ONLY:
        return serializer(value_type)
    raise TypeError(
        f"index {key!r}: {serializer.__name__} cannot be built from the value type alone"
    )


def index_class(
    key: str,
    *,
    serializer_instance: Any,
    engine: type,
    base: type,
    module: str,
    attributes: dict[str, Any],
) -> type:
    suffix = "".join(char if char.isalnum() else "_" for char in key)

    def __init__(self: Any, engine_instance: object) -> None:
        if not isinstance(engine_instance, engine):
            raise TypeError(f"expected {engine.__name__}, got {type(engine_instance).__name__}")
        self.engine = engine_instance

    namespace: dict[str, Any] = {
        "__module__": module,
        "serializer": serializer_instance,
        "key": key,
        "engine": engine,
        "__init__": __init__,
    }
    namespace.update(attributes)
    return type(f"{base.__name__}_{suffix}", (base,), namespace)


def _is_subclass(declared: Any, parent: Any) -> bool:
    if not isinstance(declared, type):
        return False
    origin = get_origin(parent)
    parent_type = origin if isinstance(origin, type) else parent
    if not isinstance(parent_type, type):
        return False
    try:
        return issubclass(declared, parent_type)
    except TypeError:
        return False


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
