"""
Application configuration for jlog.
"""

import logging
from pathlib import Path
from typing import ClassVar

from pydantic import DirectoryPath, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Validated runtime configuration for jlog.

    Values may be provided explicitly, through environment variables,
    or through a .env file.
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="JLOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,  # Make the validator separately reject an explicitly supplied blank string.
        extra="forbid",  # An unknown setting, including a misspelling will be ignored.
        frozen=True,  # After construction, configuration cannot be reassigned.
    )

    vault_path: DirectoryPath
    daily_folder: Path = Path("1. Logs/Daily")

    @field_validator("vault_path", mode="before")
    @classmethod
    def normalize_vault_path(cls, value: object) -> Path:
        """
        Expand and normalize the configured vault path.
        """

        if isinstance(value, str):
            if not value.strip():
                raise ValueError("Vault path must not be empty.")

            # .resolve() makes the path absolute, resolving any symlinks.
            return Path(value).expanduser().resolve(strict=False)

        if isinstance(value, Path):
            return value.expanduser().resolve(strict=False)

        raise ValueError("Vault path must be a string or pathlib.Path.")

    @field_validator("daily_folder", mode="before")
    @classmethod
    def validate_daily_folder(cls, value: object) -> Path:
        """
        Validate the daily notes directory relative to the vault.
        """

        if isinstance(value, str):
            if not value.strip():
                raise ValueError("Daily notes folder must not be empty.")
            path = Path(value)
        elif isinstance(value, Path):
            path = value
        else:
            raise ValueError("Daily notes folder must be a string or pathlib.Path.")

        if path == Path("."):
            raise ValueError("Daily notes folder must not refer to the vault root.")

        if path.is_absolute():
            raise ValueError("Daily folder must be relative to the vault.")

        if ".." in path.parts:
            raise ValueError("Daily folder must not contain parent directory references.")

        return path


def get_settings() -> Settings:
    """
    Load and validate the application settings.
    """

    logger.debug("Loading application settings.")

    # The required field is supplied by Pydantic Settings sources.
    return Settings()  # pyright: ignore[reportCallIssue]
