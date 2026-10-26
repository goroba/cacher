import cacher
import pytest
from pydantic import BaseModel, ValidationError

from cacher.serializers.pydantic_serializer import PydanticSerializer


class Address(BaseModel):
    city: str


class User(BaseModel):
    id: int
    address: Address


def test_json_model_round_trip() -> None:
    serializer = PydanticSerializer(User)
    user = User(id=1, address=Address(city="Paris"))
    assert serializer.deserialize(serializer.serialize(user)) == user


def test_json_model_rejects_non_instance() -> None:
    serializer = PydanticSerializer(User)
    with pytest.raises(ValueError):
        serializer.serialize(Address(city="Paris"))  # type: ignore[arg-type]


def test_json_model_invalid_json_raises_validation_error() -> None:
    serializer = PydanticSerializer(User)
    with pytest.raises(ValidationError):
        serializer.deserialize("{")


def test_json_model_rejects_non_model() -> None:
    with pytest.raises(TypeError):
        PydanticSerializer(dict)  # type: ignore[type-var]


def test_public_api_omits_pydantic_serializer() -> None:
    assert "PydanticSerializer" not in cacher.__all__
    assert not hasattr(cacher, "PydanticSerializer")
