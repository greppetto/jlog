"""
Filesystem path conventions and resolution for jlog.

Daily notes use the following convent:
    YYYY-MM-DD-Weekday.md

For example:
    2026-08-11-Tuesday.md

Weekday names are always in English and are resolved independently of the system locale.
"""

import logging
from datetime import date
from pathlib import Path

from jlog.config import Settings
from jlog.templates import render_daily_note
from jlog.utils import get_weekday_name

DEFAULT_CACHE_SUBDIRECTORY = "jlog"
DAILY_NOTE_FILENAME_PATTERN = "{date}-{weekday}.md"

logger = logging.getLogger(__name__)


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


def ensure_daily_note(settings: Settings, day: date) -> Path:
    """
    Ensure that a daily note exists and return its path.
    """

    note_path = get_daily_note_path(settings, day)

    note_path.parent.mkdir(parents=True, exist_ok=True)

    document = render_daily_note(day)

    try:
        with note_path.open(
            mode="x", encoding="utf-8", newline="\n"
        ) as file:  # mode="x" is exclusive creation (creates if file doesn't exist, raises if it does).
            file.write(document)
    except FileExistsError:
        logger.debug("Daily note already exists: %s", note_path)
    else:
        logger.debug("Created daily note: %s", note_path)

    return note_path
