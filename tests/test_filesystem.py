from datetime import date
from pathlib import Path

import pytest

from jlog.config import Settings
from jlog.filesystem import get_daily_note_filename, get_daily_note_path


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 8, 10), "2026-08-10-Monday.md"),
        (date(2026, 8, 11), "2026-08-11-Tuesday.md"),
        (date(2026, 8, 12), "2026-08-12-Wednesday.md"),
        (date(2026, 8, 13), "2026-08-13-Thursday.md"),
        (date(2026, 8, 14), "2026-08-14-Friday.md"),
        (date(2026, 8, 15), "2026-08-15-Saturday.md"),
        (date(2026, 8, 16), "2026-08-16-Sunday.md"),
        (date(2026, 1, 5), "2026-01-05-Monday.md"),
        (date(2028, 2, 29), "2028-02-29-Tuesday.md"),
        (date(2026, 12, 31), "2026-12-31-Thursday.md"),
        (date(2027, 1, 1), "2027-01-01-Friday.md"),
    ],
)
def test_daily_note_filename(day: date, expected: str) -> None:
    assert get_daily_note_filename(day) == expected


def test_daily_note_path_uses_default_daily_folder(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 11)

    result = get_daily_note_path(settings, day)

    assert result == tmp_path / "1. Logs/Daily" / "2026-08-11-Tuesday.md"


def test_daily_note_path_uses_custom_daily_folder(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path, daily_folder=Path("Journal/Daily"))
    day = date(2026, 8, 11)

    result = get_daily_note_path(settings, day)

    assert result == tmp_path / "Journal" / "Daily" / "2026-08-11-Tuesday.md"


def test_daily_note_path_does_not_create_directory(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 11)

    result = get_daily_note_path(settings, day)

    assert not result.parent.exists()


def test_daily_note_path_does_not_create_file(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 11)

    result = get_daily_note_path(settings, day)

    assert not result.exists()
