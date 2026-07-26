"""
Smoke tests for the jlog package.
"""

import importlib


def test_package_can_be_imported() -> None:
    """
    The installed jlog package should be importable.
    """

    package = importlib.import_module("jlog")

    assert package.__name__ == "jlog"


def test_cli_module_exposes_callable_main() -> None:
    """
    The configured CLI module should expose a callable main function.
    """

    cli_module = importlib.import_module("jlog.cli")
    main = getattr(cli_module, "main", None)

    assert callable(main)
