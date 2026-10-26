from collections.abc import Mapping, Sequence

import pytest

from cacher import (
    AsyncEngine,
    AsyncIndex,
    Engine,
    Index,
    IntSerializer,
    get_async_index,
    get_index,
)


class UserEngine:
    pass


class AsyncUserEngine:
    pass


user_engine = UserEngine()
async_user_engine = AsyncUserEngine()


class UserIndex(Index):
    identifier = int
    model = int
    serializer = IntSerializer()
    key = "users"
    engine = user_engine


class AsyncUserIndex(AsyncIndex):
    identifier = int
    model = int
    serializer = IntSerializer()
    key = "users"
    engine = async_user_engine


class IncompleteIndex:
    identifier = int
    model = int


def test_index_registry() -> None:
    assert isinstance(UserIndex(), Index)
    assert isinstance(AsyncUserIndex(), AsyncIndex)
    assert UserIndex.engine is user_engine
    assert AsyncUserIndex.engine is async_user_engine
    assert not isinstance(IncompleteIndex(), Index)
    assert get_index("users") is UserIndex
    assert get_async_index("users") is AsyncUserIndex
    with pytest.raises(KeyError):
        get_index("missing")
    with pytest.raises(KeyError):
        get_async_index("missing")


def test_duplicate_index_key() -> None:
    with pytest.raises(ValueError):
        class DuplicateUserIndex(Index):
            identifier = int
            model = int
            serializer = IntSerializer()
            key = "users"
            engine = UserEngine()


class MemoryHash:
    def get(self, name: str, field: str) -> str | None:
        return None

    def set(self, name: str, field: str, value: str, *, ttl: int | None = None) -> None:
        return None

    def delete(self, name: str, field: str) -> None:
        return None

    def exists(self, name: str, field: str) -> bool:
        return False

    def mget(self, name: str, fields: Sequence[str]) -> list[str | None]:
        return [None for _ in fields]

    def mset(self, name: str, items: Mapping[str, str], *, ttl: int | None = None) -> None:
        return None


class AsyncMemoryHash:
    async def get(self, name: str, field: str) -> str | None:
        return None

    async def set(self, name: str, field: str, value: str, *, ttl: int | None = None) -> None:
        return None

    async def delete(self, name: str, field: str) -> None:
        return None

    async def exists(self, name: str, field: str) -> bool:
        return False

    async def mget(self, name: str, fields: Sequence[str]) -> list[str | None]:
        return [None for _ in fields]

    async def mset(self, name: str, items: Mapping[str, str], *, ttl: int | None = None) -> None:
        return None


def test_engine_protocols() -> None:
    assert isinstance(MemoryHash(), Engine)
    assert isinstance(AsyncMemoryHash(), AsyncEngine)


def test_public_api_omits_redis_engines() -> None:
    import cacher

    assert "RedisStringEngine" not in cacher.__all__
    assert not hasattr(cacher, "RedisStringEngine")
    assert "RedisHashEngine" not in cacher.__all__
    assert not hasattr(cacher, "RedisHashEngine")
