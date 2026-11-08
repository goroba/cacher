import asyncio
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
    get_registry,
)


class UserClient:
    pass


class AsyncUserClient:
    pass


class UserStorage:
    def __init__(self) -> None:
        self.data: dict[tuple[str, str], str] = {}

    def get(self, client: UserClient, name: str, field: str) -> str | None:
        return self.data.get((name, field))

    def set(
        self, client: UserClient, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        self.data[(name, field)] = value


class AsyncUserStorage:
    def __init__(self) -> None:
        self.data: dict[tuple[str, str], str] = {}

    async def get(self, client: AsyncUserClient, name: str, field: str) -> str | None:
        return self.data.get((name, field))

    async def set(
        self,
        client: AsyncUserClient,
        name: str,
        field: str,
        value: str,
        *,
        ttl: int | None = None,
    ) -> None:
        self.data[(name, field)] = value


user_storage = UserStorage()
async_user_storage = AsyncUserStorage()


class UserIndex(KeyValueIndex):
    identifier = int
    model = int
    serializer = IntSerializer()
    key = "users"
    client_type = UserClient
    storage = user_storage


class AsyncUserIndex(AsyncKeyValueIndex):
    identifier = int
    model = int
    serializer = IntSerializer()
    key = "users"
    client_type = AsyncUserClient
    storage = async_user_storage


class IncompleteIndex:
    identifier = int
    model = int


def test_index_registry() -> None:
    index = get_registry(UserClient).get("users")
    async_index = get_registry(AsyncUserClient).get("users")
    assert isinstance(index, UserIndex)
    assert isinstance(async_index, AsyncUserIndex)
    assert isinstance(index, KeyValueIndex)
    assert isinstance(async_index, AsyncKeyValueIndex)
    assert index.storage is user_storage
    assert async_index.storage is async_user_storage
    assert not isinstance(IncompleteIndex(), KeyValueIndex)
    with pytest.raises(KeyError):
        get_registry(UserClient).get("missing")
    with pytest.raises(KeyError):
        get_registry(AsyncUserClient).get("missing")

    client = UserClient()
    assert index.get(client, 1) is None
    index.set(client, 1, 7)
    assert index.get(client, 1) == 7

    async def scenario() -> None:
        async_client = AsyncUserClient()
        assert await async_index.get(async_client, 1) is None
        await async_index.set(async_client, 1, 8)
        assert await async_index.get(async_client, 1) == 8

    asyncio.run(scenario())


class UnusedClient:
    pass


def test_get_registry() -> None:
    assert isinstance(get_registry(UserClient).get("users"), UserIndex)
    assert isinstance(get_registry(AsyncUserClient).get("users"), AsyncUserIndex)
    with pytest.raises(KeyError, match="no index 'missing' registered for UserClient"):
        get_registry(UserClient).get("missing")
    with pytest.raises(KeyError, match="no index 'missing' registered for AsyncUserClient"):
        get_registry(AsyncUserClient).get("missing")


def test_unknown_client_has_no_registry() -> None:
    with pytest.raises(KeyError, match="no indexes registered for UnusedClient"):
        get_registry(UnusedClient)


def test_duplicate_index_key() -> None:
    with pytest.raises(ValueError):
        class DuplicateUserIndex(KeyValueIndex):
            identifier = int
            model = int
            serializer = IntSerializer()
            key = "users"
            client_type = UserClient
            storage = UserStorage()
    with pytest.raises(ValueError):
        class DuplicateAsyncUserIndex(AsyncKeyValueIndex):
            identifier = int
            model = int
            serializer = IntSerializer()
            key = "users"
            client_type = AsyncUserClient
            storage = AsyncUserStorage()


class MemoryHash:
    def get(self, client: object, name: str, field: str) -> str | None:
        return None

    def set(
        self, client: object, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        return None

    def delete(self, client: object, name: str, field: str) -> None:
        return None

    def exists(self, client: object, name: str, field: str) -> bool:
        return False

    def mget(self, client: object, name: str, fields: Sequence[str]) -> list[str | None]:
        return [None for _ in fields]

    def mset(
        self, client: object, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        return None


class AsyncMemoryHash:
    async def get(self, client: object, name: str, field: str) -> str | None:
        return None

    async def set(
        self, client: object, name: str, field: str, value: str, *, ttl: int | None = None
    ) -> None:
        return None

    async def delete(self, client: object, name: str, field: str) -> None:
        return None

    async def exists(self, client: object, name: str, field: str) -> bool:
        return False

    async def mget(self, client: object, name: str, fields: Sequence[str]) -> list[str | None]:
        return [None for _ in fields]

    async def mset(
        self, client: object, name: str, items: Mapping[str, str], *, ttl: int | None = None
    ) -> None:
        return None


class MemorySet:
    def add(self, client: object, name: str, member: str) -> None:
        return None

    def madd(self, client: object, name: str, members: Sequence[str]) -> None:
        return None

    def remove(self, client: object, name: str, member: str) -> None:
        return None

    def mremove(self, client: object, name: str, members: Sequence[str]) -> None:
        return None

    def contains(self, client: object, name: str, member: str) -> bool:
        return False


class AsyncMemorySet:
    async def add(self, client: object, name: str, member: str) -> None:
        return None

    async def madd(self, client: object, name: str, members: Sequence[str]) -> None:
        return None

    async def remove(self, client: object, name: str, member: str) -> None:
        return None

    async def mremove(self, client: object, name: str, members: Sequence[str]) -> None:
        return None

    async def contains(self, client: object, name: str, member: str) -> bool:
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
