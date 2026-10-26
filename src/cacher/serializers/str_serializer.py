"""String serializer."""

from cacher.serializers.serializer import Serializer


class StrSerializer(Serializer[str, str]):
    """Identity serializer, including the empty string."""

    def serialize(self, value: str) -> str:
        return value

    def deserialize(self, value: str) -> str:
        return value
