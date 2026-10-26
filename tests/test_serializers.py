from dataclasses import dataclass
from datetime import date, datetime, timezone

import pytest

from cacher import (
    BoolSerializer,
    DataclassSerializer,
    DatetimeSerializer,
    DictSerializer,
    FloatSerializer,
    IntSerializer,
    StrSerializer,
)


def test_int_round_trip() -> None:
    serializer = IntSerializer()
    assert serializer.deserialize(serializer.serialize(0)) == 0
    assert serializer.deserialize(serializer.serialize(-42)) == -42
    assert serializer.serialize(15) == "15"


def test_int_rejects_bool() -> None:
    serializer = IntSerializer()
    with pytest.raises(ValueError):
        serializer.serialize(True)
    with pytest.raises(ValueError):
        serializer.serialize(False)


def test_int_rejects_invalid_text() -> None:
    serializer = IntSerializer()
    with pytest.raises(ValueError):
        serializer.deserialize("nope")
    with pytest.raises(ValueError):
        serializer.deserialize("1.5")
    with pytest.raises(ValueError):
        serializer.deserialize(True)  # type: ignore[arg-type]


def test_float_round_trip() -> None:
    serializer = FloatSerializer()
    for value in (0.0, -2.5, 0.1):
        assert serializer.deserialize(serializer.serialize(value)) == value


def test_float_rejects_invalid_text() -> None:
    with pytest.raises(ValueError):
        FloatSerializer().deserialize("nope")


def test_str_round_trip() -> None:
    serializer = StrSerializer()
    assert serializer.serialize("") == ""
    assert serializer.deserialize("") == ""
    assert serializer.deserialize(serializer.serialize("café")) == "café"


def test_bool_round_trip() -> None:
    serializer = BoolSerializer()
    assert serializer.serialize(True) == "true"
    assert serializer.serialize(False) == "false"
    assert serializer.deserialize("true") is True
    assert serializer.deserialize("false") is False


def test_datetime_round_trip() -> None:
    serializer = DatetimeSerializer()
    values = (
        datetime(2026, 1, 1),
        datetime(2026, 1, 1, 12, 30, 45, 123456),
        datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
    )
    for value in values:
        assert serializer.deserialize(serializer.serialize(value)) == value
    assert serializer.serialize(datetime(2026, 1, 1, tzinfo=timezone.utc)) == (
        "2026-01-01T00:00:00+00:00"
    )


def test_datetime_rejects_non_datetime() -> None:
    serializer = DatetimeSerializer()
    with pytest.raises(ValueError):
        serializer.serialize(date(2026, 1, 1))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        serializer.serialize("2026-01-01T00:00:00")  # type: ignore[arg-type]


def test_datetime_rejects_invalid_text() -> None:
    serializer = DatetimeSerializer()
    with pytest.raises(ValueError):
        serializer.deserialize("nope")
    with pytest.raises(ValueError):
        serializer.deserialize(2026)  # type: ignore[arg-type]


def test_bool_rejects_invalid_text() -> None:
    serializer = BoolSerializer()
    with pytest.raises(ValueError):
        serializer.deserialize("1")
    with pytest.raises(ValueError):
        serializer.deserialize("True")
    with pytest.raises(ValueError):
        serializer.deserialize("yes")


def test_json_dict_round_trip() -> None:
    serializer = DictSerializer()
    value = {"name": "café", "n": 1, "ok": True, "items": [None, {"k": "v"}]}
    raw = serializer.serialize(value)
    assert "café" in raw
    assert ": " not in raw
    assert serializer.deserialize(raw) == value


def test_json_dict_rejects_non_object() -> None:
    serializer = DictSerializer()
    with pytest.raises(ValueError):
        serializer.serialize(["nope"])  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        serializer.deserialize("[]")
    with pytest.raises(ValueError):
        serializer.deserialize("{")


@dataclass
class Address:
    city: str


@dataclass
class Tag:
    name: str


@dataclass
class User:
    id: int
    address: Address
    tags: list[Tag]
    stops: tuple[Address, ...]
    note: Address | None = None
    role: str = "member"


@dataclass
class Event:
    at: datetime


def test_json_dataclass_round_trip() -> None:
    serializer = DataclassSerializer(User)
    user = User(
        id=1,
        address=Address(city="Paris"),
        tags=[Tag(name="a"), Tag(name="b")],
        stops=(Address(city="Lyon"),),
        note=None,
    )
    assert serializer.deserialize(serializer.serialize(user)) == user


def test_json_dataclass_defaults_and_unknown_keys() -> None:
    serializer = DataclassSerializer(User)
    restored = serializer.deserialize(
        '{"id":1,"address":{"city":"Paris"},"tags":[],"stops":[],"extra":true}'
    )
    assert restored.role == "member"
    assert restored.note is None
    assert restored.tags == []
    assert not hasattr(restored, "extra")


def test_json_dataclass_rejects_non_dataclass() -> None:
    with pytest.raises(TypeError):
        DataclassSerializer(dict)  # type: ignore[arg-type]


def test_json_dataclass_rejects_non_json_value() -> None:
    with pytest.raises(ValueError):
        DataclassSerializer(Event).serialize(Event(at=datetime(2026, 1, 1)))
