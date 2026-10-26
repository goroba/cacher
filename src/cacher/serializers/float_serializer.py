"""Float serializer."""

from cacher.serializers.serializer import Serializer


class FloatSerializer(Serializer[float, str]):
    """Float text via ``repr``, which round-trips finite floats."""

    def serialize(self, value: float) -> str:
        return repr(value)

    def deserialize(self, value: str) -> float:
        if isinstance(value, bool) or not isinstance(value, str):
            raise ValueError(f"invalid float: {value!r}")
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"invalid float: {value!r}") from exc
