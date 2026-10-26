"""Serializer protocol."""

from typing import Protocol


class Serializer[ValueType, StorageType](Protocol):
    """Convert a Python value to a storage value and back."""

    def serialize(self, value: ValueType) -> StorageType:
        """Convert ``value`` into its storage representation."""
        ...

    def deserialize(self, value: StorageType) -> ValueType:
        """Restore a Python value from its storage representation."""
        ...
