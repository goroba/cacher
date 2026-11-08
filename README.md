# cacher

A Python library.

**What is it for?** Cacher is a way to name a cache binding and use it from application code. An index holds one storage key, a serializer, and a storage. You build it once. Each call takes your storage client and reads or writes a Python value through that binding. Redis storages are included. Any storage that matches the protocol works the same way.

**What can an index store?** A key-value index stores one model per id. A set index stores members in one set. Each has a sync builder and an async builder.

## Indexes

Build an index once with `build_async_key_value_index` or `build_async_set_index`. Pass a key, the value type, a serializer instance, and a storage instance. Then pass a storage client into every call.

```python
from uuid import UUID

from pydantic import BaseModel
from redis.asyncio import Redis as AsyncRedis

from cacher import build_async_key_value_index
from cacher.serializers.pydantic_serializer import PydanticSerializer
from cacher.storage import AsyncRedisHashStorage

class User(BaseModel):
    id: UUID
    name: str

ada = User(id=UUID("12345678-1234-5678-1234-567812345678"), name="Ada")

users = build_async_key_value_index(
    "users",
    id_type=UUID,
    model_type=User,
    serializer=PydanticSerializer(User),
    storage=AsyncRedisHashStorage(),
)

async def main() -> None:
    client = AsyncRedis(decode_responses=True)
    await users.set(client, ada.id, ada, ttl=60)
    value = await users.get(client, ada.id)
    await users.delete(client, ada.id)
```

`ttl` is a whole number of seconds on `set` and `mset`. Omit it, or pass `None`, and the write does not expire. `mset` applies that one TTL to every id. `delete` removes one id. A missing id is not an error.

Inside `main`, the same client works for a set index.

```python
from cacher import IntSerializer, build_async_set_index
from cacher.storage import AsyncRedisSetStorage

active = build_async_set_index(
    "active_users",
    member_type=int,
    serializer=IntSerializer(),
    storage=AsyncRedisSetStorage(),
)

    await active.add(client, 1)
    present = await active.contains(client, 1)
    await active.remove(client, 1)
```

`remove` drops one member. A missing member is not an error. Sets have no TTL.

Sync indexes use `build_key_value_index` and `build_set_index` with the matching sync storage. Those calls are not awaited.

`get_registry` from `cacher` returns that index: `get_registry(AsyncRedis).get("users")`.

## Install

```bash
pip install cacher
pip install "cacher[redis]"
pip install "cacher[pydantic]"
pip install "cacher[redis,pydantic]"
```

From a checkout, the same extras are:

```bash
pip install -e ".[dev]"
pip install -e ".[redis]"
pip install -e ".[redis,pydantic]"
```

Runtime dependencies live in `pyproject.toml` under `[project] dependencies`. Optional Redis and Pydantic support, and the test tools, live in extras. A plain install does not pull Redis or Pydantic. There is no `requirements.txt`.

## Test

```bash
pytest
```

## Publish

When the package is ready for PyPI, build and upload it. Confirm the project name is free on PyPI first, and fill in the author details in `pyproject.toml`.

```bash
pip install build twine
python -m build
twine upload dist/*
```
