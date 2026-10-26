"""Boolean serializer."""

from cacher.serializers.serializer import Serializer


class BoolSerializer(Serializer[bool, str]):
    """``True`` and ``False`` as ``"true"`` and ``"false"``."""

    def serialize(self, value: bool) -> str:
        if value is True:
            return "true"
        if value is False:
            return "false"
        raise ValueError(f"expected bool, got {type(value).__name__}")

    def deserialize(self, value: str) -> bool:
        if value == "true":
            return True
        if value == "false":
            return False
        raise ValueError(f"invalid bool: {value!r}")
