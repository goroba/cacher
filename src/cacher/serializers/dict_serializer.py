"""Dict JSON serializer."""

import json
from typing import Any

from cacher.serializers.serializer import Serializer


class DictSerializer(Serializer[dict[str, Any], str]):
    """JSON object text for a dict."""

    def serialize(self, value: dict[str, Any]) -> str:
        if not isinstance(value, dict):
            raise ValueError(f"expected dict, got {type(value).__name__}")
        try:
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except TypeError as exc:
            raise ValueError("value is not JSON serializable") from exc

    def deserialize(self, value: str) -> dict[str, Any]:
        if not isinstance(value, str):
            raise ValueError(f"invalid JSON: {value!r}")
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {value!r}") from exc
        if not isinstance(loaded, dict):
            raise ValueError(f"expected JSON object, got {type(loaded).__name__}")
        return loaded
