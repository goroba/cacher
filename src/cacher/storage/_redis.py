"""Redis client import and value decoding. Requires the ``redis`` extra."""

try:
    from redis import Redis
    from redis.asyncio import Redis as AsyncRedis
except ImportError as exc:
    raise ImportError(
        "Redis support is not installed. Install it with: pip install 'cacher[redis]'"
    ) from exc


def decode(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8")
    raise TypeError(f"unexpected Redis value type: {type(value).__name__}")


__all__ = ["AsyncRedis", "Redis", "decode"]
