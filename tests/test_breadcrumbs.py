import pytest

from cacher.breadcrumbs import ColonBreadcrumbs


def test_colon_round_trip() -> None:
    breadcrumbs = ColonBreadcrumbs()
    assert breadcrumbs.encode("users", "42") == "users:42"
    assert breadcrumbs.decode("users:42") == ("users", "42")
    assert breadcrumbs.decode(breadcrumbs.encode("users", "42")) == ("users", "42")


def test_colon_identifier_may_contain_colon() -> None:
    breadcrumbs = ColonBreadcrumbs()
    assert breadcrumbs.encode("users", "a:b") == "users:a:b"
    assert breadcrumbs.decode("users:a:b") == ("users", "a:b")
    assert breadcrumbs.decode(breadcrumbs.encode("users", "a:b")) == ("users", "a:b")


def test_colon_rejects_missing_separator() -> None:
    with pytest.raises(ValueError):
        ColonBreadcrumbs().decode("users")
