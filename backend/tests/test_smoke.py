"""Baseline check that the test runner and package import work (T0.4)."""

import inai_backend


def test_package_imports() -> None:
    assert inai_backend.__doc__ == "Inai MVP backend."
