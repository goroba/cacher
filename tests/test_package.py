from importlib.metadata import requires

import cacher


def test_import() -> None:
    assert cacher.__version__


def test_optional_extras() -> None:
    declared = requires("cacher") or []
    extras = {
        requirement.split("extra == ")[-1].strip().strip("'\"")
        for requirement in declared
        if "extra ==" in requirement
    }
    assert {"redis", "pydantic"} <= extras
