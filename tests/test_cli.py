"""
Smoke tests for the installed jlog command.
"""

# import argparse
import logging
import shutil
import subprocess
from collections.abc import Sequence

import pytest

from jlog.cli import configure_logging


def run_jlog(arguments: Sequence[str] = ()) -> subprocess.CompletedProcess[str]:
    """
    Run the installed jlog command and capture its output.
    """

    # uv makes the project’s virtual-environment executables available, resolving correctly based on platform
    executable = shutil.which("jlog")

    assert executable is not None, (
        "The jlog console script was not found. Run the tests through the project environment such as `uv run pytest`."
    )

    # The command is passed as a list rather than a shell string
    # This is safer and more portable than using shell=True
    return subprocess.run(
        [executable, *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def test_help_exits_successfully() -> None:
    """
    The --help option should display help and exit successfully.
    """

    result = run_jlog(["--help"])

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "jlog" in result.stdout.lower()
    # Since help is a normal output, it should appear on standard output rather than standard error
    assert result.stderr == ""


def test_license_exits_successfully() -> None:
    """
    The --license option should display license and exit successfully.
    """

    result = run_jlog(["--license"])

    assert result.returncode == 0
    assert "license" in result.stdout.lower()
    assert "arlecchino" in result.stdout.lower()
    assert result.stderr == ""


def test_no_arguments_displays_help() -> None:
    """
    Running jlog without arguments should display help successfully.
    """

    result = run_jlog()

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "jlog" in result.stdout.lower()
    assert result.stderr == ""


def test_configure_logging_rejects_verbose_and_quiet_together() -> None:
    """
    Verbose and quiet are mutually exclusive and should not be true at the same time.
    """

    result = run_jlog(["-v", "-q"])

    assert result.returncode != 0
    assert result.stdout == ""
    assert "jlog" in result.stderr.lower()
    assert "not allowed with" in result.stderr.lower()


def test_configure_logging_default_to_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Running jlog without verbose and quiet should result in logging defaulting to WARNING.
    """

    calls = {}

    def fake_base_config(**kwargs):
        calls.update(kwargs)

    monkeypatch.setattr(logging, "basicConfig", fake_base_config)

    configure_logging(verbose=False, quiet=False)

    assert calls["level"] == logging.WARNING


def test_configure_logging_verbose_uses_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Running jlog with verbose should result in logging defaulting to DEBUG.
    """

    calls = {}

    def fake_base_config(**kwargs):
        calls.update(kwargs)

    monkeypatch.setattr(logging, "basicConfig", fake_base_config)

    configure_logging(verbose=True, quiet=False)

    assert calls["level"] == logging.DEBUG


def test_configure_logging_quiet_uses_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Running jlog with quiet should result in logging defaulting to ERROR.
    """

    calls = {}

    def fake_base_config(**kwargs):
        calls.update(kwargs)

    monkeypatch.setattr(logging, "basicConfig", fake_base_config)

    configure_logging(verbose=False, quiet=True)

    assert calls["level"] == logging.ERROR
