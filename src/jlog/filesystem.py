"""
Filesystem path conventions and resolution for jlog.

Daily notes use the following convent:
    YYYY-MM-DD-Weekday.md

For example:
    2026-08-11-Tuesday.md

Weekday names are always in English and are resolved independently of the system locale.
"""

import os
import threading
from datetime import date
from pathlib import Path
from types import TracebackType

from platformdirs import user_cache_dir, user_downloads_dir

from jlog.config import Settings

DEFAULT_CACHE_SUBDIRECTORY = "jlog"
WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
DAILY_NOTE_FILENAME_PATTERN = "{date}-{weekday}.md"


def get_weekday_name(day: date) -> str:
    """
    Return the English weekday name for a calendar date.
    """

    return WEEKDAYS[day.weekday()]


def get_daily_note_filename(day: date) -> str:
    """
    Return the daily note filename for a calendar date.
    """

    return DAILY_NOTE_FILENAME_PATTERN.format(date=day.isoformat(), weekday=get_weekday_name(day))


def get_daily_note_path(settings: Settings, day: date) -> Path:
    """
    Return the path for a daily note without creating it.
    """

    return settings.vault_path / settings.daily_folder / get_daily_note_filename(day)


class SimpleFileLock:
    """
    Cross-platform file lock.
    """

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def __enter__(self):
        self._lock.acquire()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(f"pid:{os.getpid()}\n")
        return self

    def __exit__(
        self,
        execution_type: type[BaseException] | None,
        execution_value: type[BaseException] | None,
        execution_traceback: TracebackType,
    ):
        try:
            if self.path.exists():
                try:
                    self.path.unlink()
                except Exception:
                    pass
        finally:
            self._lock.release()


def _resolve_directory(path_string: str | None, default: Path) -> Path:
    if path_string:
        try:
            path = Path(path_string).expanduser().resolve()
            path.mkdir(parents=True, exist_ok=True)
            return path
        except TypeError, ValueError, OSError:
            pass
    default.mkdir(parents=True, exist_ok=True)
    return default


def resolve_output_directory(output_directory: str | None = None) -> Path:
    """
    Figures out where to place the output files.
    """

    default = Path(user_downloads_dir())
    return _resolve_directory(output_directory, default)


def resolve_cache_directory(cache_directory: str | None = None) -> Path:
    """
    Figures out where to place the cache files.
    """

    default = Path(user_cache_dir())
    return _resolve_directory(cache_directory, default)
