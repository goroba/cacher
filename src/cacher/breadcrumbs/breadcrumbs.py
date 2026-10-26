"""Breadcrumbs protocol."""

from typing import Protocol


class Breadcrumbs(Protocol):
    """Encode an index and an identifier into one string, and split that string back."""

    def encode(self, index: str, identifier: str) -> str:
        """Join ``index`` and ``identifier`` into one string."""
        ...

    def decode(self, value: str) -> tuple[str, str]:
        """Split ``value`` into the index and the identifier."""
        ...
