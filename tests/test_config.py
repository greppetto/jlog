"""
Tests for the configuration object.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from jlog.config import Settings


def test_settings_accepts_existing_directory(tmp_path: Path) -> None:
    """
    The settings object should accept any valid directory.
    """

    settings = Settings(vault_path=tmp_path)

    assert settings.vault_path == tmp_path
    assert isinstance(settings.vault_path, Path)


def test_settings_loads_vault_path_from_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object should be able to load the vault path from the environment variables.
    """

    monkeypatch.setenv("JLOG_VAULT_PATH", str(tmp_path))

    settings = Settings()  # pyright: ignore[reportCallIssue]

    assert settings.vault_path == tmp_path


def test_settings_loads_vault_path_from_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object should be able to load the vault path from dotenv files in the current working directory.
    """

    monkeypatch.chdir(tmp_path)

    (tmp_path / ".env").write_text(f"JLOG_VAULT_PATH={tmp_path}\n", encoding="utf-8")

    settings = Settings()  # pyright: ignore[reportCallIssue]

    assert settings.vault_path == tmp_path


def test_environment_overrides_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object should correctly pick the vault path from its corresponding environment variable instead of a dotenv file, if the environment variable is present.
    """

    dotenv_vault = tmp_path / "dotenv-vault"
    environment_vault = tmp_path / "environment-vault"

    dotenv_vault.mkdir()
    environment_vault.mkdir()

    monkeypatch.chdir(tmp_path)

    (tmp_path / ".env").write_text(f"JLOG_VAULT_PATH={tmp_path}\n", encoding="utf-8")

    monkeypatch.setenv("JLOG_VAULT_PATH", str(environment_vault))

    settings = Settings()  # pyright: ignore[reportCallIssue]

    assert settings.vault_path == environment_vault


def test_explicit_value_overrides_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object should correctly choose the vault path to be the explicitly passed value instead of from the environment.
    """

    environment_vault = tmp_path / "environment-vault"
    explicit_vault = tmp_path / "explicit-vault"

    environment_vault.mkdir()
    explicit_vault.mkdir()

    monkeypatch.setenv("JLOG_VAULT_PATH", str(environment_vault))

    settings = Settings(vault_path=explicit_vault)

    assert settings.vault_path == explicit_vault


def test_settings_requires_vault_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object must fail if vault path is missing.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("JLOG_VAULT_PATH", raising=False)

    with pytest.raises(ValidationError):
        Settings()  # pyright: ignore[reportCallIssue]


def test_settings_rejects_nonexistent_vault_path(tmp_path: Path) -> None:
    """
    The settings object should raise if provided vault path does not exist.
    """

    nonexistent_path = tmp_path / "does-not-exist"

    with pytest.raises(ValidationError):
        Settings(vault_path=nonexistent_path)


def test_settings_rejects_file_as_vault_path(tmp_path: Path) -> None:
    """
    The settings object should raise if provided vault path is a file.
    """

    file_path = tmp_path / "not-a-vault.txt"
    file_path.write_text("This is a file.", encoding="utf-8")

    with pytest.raises(ValidationError):
        Settings(vault_path=file_path)


def test_empty_environment_variable_is_treated_as_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object must treat an empty environment variable as if it is missing.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JLOG_VAULT_PATH", "")

    with pytest.raises(ValidationError):
        Settings()  # pyright: ignore[reportCallIssue]


def test_settings_rejects_blank_explicit_vault_path() -> None:
    """
    The settings object must reject an explicitly passed blank string.
    """

    with pytest.raises(ValidationError, match="Vault path must not be empty."):
        Settings(vault_path=" ")  # pyright: ignore[reportArgumentType]


def test_daily_folder_defaults_to_logs_daily(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object should default to "1. Logs/Daily for daily folder."
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("JLOG_DAILY_FOLDER", raising=False)

    settings = Settings(vault_path=tmp_path)

    assert settings.daily_folder == Path("1. Logs/Daily")


def test_daily_folder_loads_from_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object should load daily folder from the environment, if present."
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JLOG_DAILY_FOLDER", "Journal/Daily")

    settings = Settings(vault_path=tmp_path)

    assert settings.daily_folder == Path("Journal/Daily")


def test_daily_folder_accepts_nested_relative_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object should load daily folder, even if it is a nested relative path."
    """

    monkeypatch.chdir(tmp_path)

    settings = Settings(vault_path=tmp_path, daily_folder=Path("Journal/Daily"))

    assert settings.daily_folder == Path("Journal/Daily")


def test_daily_folder_does_not_need_to_exist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object must not enforce existence of supplied daily folder.
    """
    monkeypatch.chdir(tmp_path)

    daily_folder = Path("Journal/Daily")

    settings = Settings(vault_path=tmp_path, daily_folder=daily_folder)

    assert settings.daily_folder == daily_folder
    assert not (tmp_path / daily_folder).exists()


def test_daily_folder_rejects_absolute_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object must reject an absolute path as the daily folder.
    """

    monkeypatch.chdir(tmp_path)

    absolute_path = tmp_path / "Daily"

    with pytest.raises(ValidationError, match="Daily notes folder must be relative to the vault."):
        Settings(vault_path=tmp_path, daily_folder=absolute_path)


@pytest.mark.parametrize(
    "daily_folder",
    [
        Path("../Daily"),
        Path("Journal/../Daily"),
        Path("Journal/../../Daily"),
    ],
)
def test_daily_folder_rejects_parent_directory_references(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, daily_folder: Path
) -> None:
    """
    The settings object must reject if there are any parent directory references in the supplied daily folder path.
    """
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError, match="Daily notes folder must not contain parent directory references."):
        Settings(vault_path=tmp_path, daily_folder=daily_folder)


def test_daily_folder_rejects_vault_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object must reject the vault root as the daily folder.
    """

    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValidationError, match="Daily notes folder must not refer to the vault root."):
        Settings(vault_path=tmp_path, daily_folder=Path("."))


def test_daily_folder_rejects_blank_environment_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    The settings object should reject if loaded environment value is blank."
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JLOG_DAILY_FOLDER", " ")

    with pytest.raises(ValidationError, match="Daily notes folder must not be empty."):
        Settings(vault_path=tmp_path)
