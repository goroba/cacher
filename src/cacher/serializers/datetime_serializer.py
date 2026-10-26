"""Datetime serializer."""

from datetime import datetime

from cacher.serializers.serializer import Serializer


class DatetimeSerializer(Serializer[datetime, str]):
    """ISO 8601 text via ``datetime.isoformat``."""

    def serialize(self, value: datetime) -> str:
        if not isinstance(value, datetime):
            raise ValueError(f"expected datetime, got {type(value).__name__}")
        return value.isoformat()

    def deserialize(self, value: str) -> datetime:
        if not isinstance(value, str):
            raise ValueError(f"invalid datetime: {value!r}")
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"invalid datetime: {value!r}") from exc
