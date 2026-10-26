"""Integer serializer."""

from cacher.serializers.serializer import Serializer


class IntSerializer(Serializer[int, str]):
    """Decimal integer text. ``bool`` is rejected because it is an ``int`` subclass."""

    def serialize(self, value: int) -> str:
        if isinstance(value, bool):
            raise ValueError("expected int, got bool")
        return str(value)

    def deserialize(self, value: str) -> int:
        if isinstance(value, bool) or not isinstance(value, str):
            raise ValueError(f"invalid int: {value!r}")
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"invalid int: {value!r}") from exc
