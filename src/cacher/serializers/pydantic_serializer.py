"""Pydantic serializer. Importing this module requires the ``pydantic`` extra."""

from cacher.serializers.serializer import Serializer

try:
    from pydantic import BaseModel
except ImportError as exc:
    raise ImportError(
        "Pydantic support is not installed. Install it with: pip install 'cacher[pydantic]'"
    ) from exc


class PydanticSerializer[ModelType: BaseModel](Serializer[ModelType, str]):
    """JSON text for one Pydantic ``BaseModel`` subclass."""

    def __init__(self, model: type[ModelType]) -> None:
        if not isinstance(model, type) or not issubclass(model, BaseModel):
            raise TypeError(f"expected a BaseModel subclass, got {model!r}")
        self._model = model

    def serialize(self, value: ModelType) -> str:
        if not isinstance(value, self._model):
            raise ValueError(f"expected {self._model.__name__} instance")
        return value.model_dump_json()

    def deserialize(self, value: str) -> ModelType:
        if not isinstance(value, str):
            raise ValueError(f"invalid JSON: {value!r}")
        return self._model.model_validate_json(value)
