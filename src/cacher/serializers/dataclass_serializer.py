"""Dataclass JSON serializer."""

import json
import types
from dataclasses import MISSING, asdict, fields, is_dataclass
from typing import Any, Union, get_args, get_origin, get_type_hints

from cacher.serializers.serializer import Serializer


def _dump_json(value: object) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except TypeError as exc:
        raise ValueError("value is not JSON serializable") from exc


def _load_json(value: str) -> Any:
    if not isinstance(value, str):
        raise ValueError(f"invalid JSON: {value!r}")
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {value!r}") from exc


def _is_dataclass_type(cls: object) -> bool:
    return isinstance(cls, type) and is_dataclass(cls)


def _split_optional(hint: Any) -> tuple[Any, bool]:
    origin = get_origin(hint)
    if origin is Union or origin is types.UnionType:
        args = get_args(hint)
        non_none = [arg for arg in args if arg is not type(None)]
        if len(args) == 2 and len(non_none) == 1:
            return non_none[0], True
    return hint, False


def _dataclass_collection(hint: Any) -> tuple[type[list[Any]] | type[tuple[Any, ...]], type] | None:
    origin = get_origin(hint)
    args = get_args(hint)
    if origin is list and len(args) == 1 and _is_dataclass_type(args[0]):
        return list, args[0]
    if (
        origin is tuple
        and len(args) == 2
        and args[1] is Ellipsis
        and _is_dataclass_type(args[0])
    ):
        return tuple, args[0]
    return None


def _from_json_value(hint: Any, value: Any) -> Any:
    inner, optional = _split_optional(hint)
    if optional and value is None:
        return None
    if _is_dataclass_type(inner):
        return _dataclass_from_json(inner, value)
    collection = _dataclass_collection(inner)
    if collection is not None:
        container, item_type = collection
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"expected a list of {item_type.__name__}")
        items = [_dataclass_from_json(item_type, item) for item in value]
        return container(items)
    return value


def _dataclass_from_json(cls: type, data: object) -> Any:
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object for {cls.__name__}")
    hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for field in fields(cls):
        if not field.init:
            continue
        if field.name not in data:
            if field.default is MISSING and field.default_factory is MISSING:
                raise ValueError(f"missing field {cls.__name__}.{field.name}")
            continue
        kwargs[field.name] = _from_json_value(hints.get(field.name, Any), data[field.name])
    return cls(**kwargs)


class DataclassSerializer[ModelType](Serializer[ModelType, str]):
    """JSON object text for one dataclass type."""

    def __init__(self, cls: type[ModelType]) -> None:
        if not _is_dataclass_type(cls):
            raise TypeError(f"expected a dataclass, got {cls!r}")
        self._cls = cls

    def serialize(self, value: ModelType) -> str:
        if not isinstance(value, self._cls):
            raise ValueError(f"expected {self._cls.__name__} instance")
        return _dump_json(asdict(value))

    def deserialize(self, value: str) -> ModelType:
        return _dataclass_from_json(self._cls, _load_json(value))
