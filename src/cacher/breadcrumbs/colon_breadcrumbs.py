"""Colon-separated breadcrumbs."""

from cacher.breadcrumbs.breadcrumbs import Breadcrumbs


class ColonBreadcrumbs(Breadcrumbs):
    """Join and split an index and an identifier with a colon.

    ``decode`` splits on the first colon, so an identifier may contain colons.
    """

    def encode(self, index: str, identifier: str) -> str:
        return f"{index}:{identifier}"

    def decode(self, value: str) -> tuple[str, str]:
        parts = value.split(":", 1)
        if len(parts) != 2:
            raise ValueError(f"invalid breadcrumb: {value!r}")
        index, identifier = parts
        return index, identifier
