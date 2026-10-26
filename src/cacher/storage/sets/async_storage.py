"""Asynchronous set storage."""

from collections.abc import Hashable, Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class AsyncSetStorage[MemberType: Hashable](Protocol):
    """Asynchronous set storage.

    ``name`` is the set name. ``member`` is one element of that set.
    Adding a member that is already present is not an error.
    Removing a missing member is not an error.
    """

    async def add(self, name: str, member: MemberType) -> None:
        """Add ``member`` to the set."""
        ...

    async def madd(self, name: str, members: Sequence[MemberType]) -> None:
        """Add every member."""
        ...

    async def remove(self, name: str, member: MemberType) -> None:
        """Remove ``member``. A missing member is not an error."""
        ...

    async def mremove(self, name: str, members: Sequence[MemberType]) -> None:
        """Remove every member. Missing members are not an error."""
        ...

    async def contains(self, name: str, member: MemberType) -> bool:
        """Return whether ``member`` is in the set."""
        ...
