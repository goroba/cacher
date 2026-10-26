from collections.abc import Mapping, Sequence

import pytest

from cacher import (
    AsyncKeyValueIndex,
    AsyncKeyValueStorage,
    AsyncSetStorage,
    IntSerializer,
    KeyValueIndex,
    KeyValueStorage,
    SetStorage,
    get_async_index,
    get_index,
)


class UserStorage:
    pass


class AsyncUserStorage:
    pass


user_storage = UserStorage()
async_user_storage = AsyncUserStorage()


class UserIndex(KeyValueIndex):
    identifier = int
    model = int
    serializer = IntSerializer()
    key = "users"
    storage = user_storage


class AsyncUserIndex(AsyncKeyValueIndex):
    identifier = int
    model = int
    serializer = IntSerializer()
    key = "users"
    storage = async_user_storage


class IncompleteIndex:
    identifier = int
    model = int


def test_index_registry() -> None:
    assert isinstance(UserIndex(), KeyValueIndex)
    assert isinstance(AsyncUserIndex(), AsyncKeyValueIndex)
    assert UserIndex.storage is user_storage
    assert AsyncUserIndex.storage is async_user_storage
    assert not isinstance(IncompleteIndex(), KeyValueIndex)
    assert get_index("users") is UserIndex
    assert get_async_index("users") is AsyncUserIndex
    with pytest.raises(KeyError):
        get_index("missing")
    with pytest.raises(KeyError):
        get_async_index("missing")


def test_duplicate_index_key() -> None:
    with pytest.raises(ValueError):
        class DuplicateUserIndex(KeyValueIndex):
            identifier = int
            model = int
            serializer = IntSerializer()
            key = "users"
            storage = UserStorage()
    with pytest.raises(ValueError):
        class DuplicateAsyncUserIndex(AsyncKeyValueIndex):
            identifier = int
            model = int
            serializer = IntSerializer()
            key = "users"
            storage = AsyncUserStorage()


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


class MemorySet:
    def add(self, name: str, member: str) -> None:
        return None

    def madd(self, name: str, members: Sequence[str]) -> None:
        return None

    def remove(self, name: str, member: str) -> None:
        return None

    def mremove(self, name: str, members: Sequence[str]) -> None:
        return None

    def contains(self, name: str, member: str) -> bool:
        return False


class AsyncMemorySet:
    async def add(self, name: str, member: str) -> None:
        return None

    async def madd(self, name: str, members: Sequence[str]) -> None:
        return None

    async def remove(self, name: str, member: str) -> None:
        return None

    async def mremove(self, name: str, members: Sequence[str]) -> None:
        return None

    async def contains(self, name: str, member: str) -> bool:
        return False


def test_storage_protocols() -> None:
    assert isinstance(MemoryHash(), KeyValueStorage)
    assert isinstance(AsyncMemoryHash(), AsyncKeyValueStorage)
    assert isinstance(MemorySet(), SetStorage)
    assert isinstance(AsyncMemorySet(), AsyncSetStorage)


def test_public_api_omits_redis_storages() -> None:
    import cacher

    for name in (
        "RedisStringStorage",
        "RedisHashStorage",
        "RedisSetStorage",
        "AsyncRedisStringStorage",
        "AsyncRedisHashStorage",
        "AsyncRedisSetStorage",
    ):
        assert name not in cacher.__all__
        assert not hasattr(cacher, name)
