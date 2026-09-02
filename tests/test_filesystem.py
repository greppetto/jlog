import os
import stat
from datetime import date
from pathlib import Path

import pytest

from jlog.config import Settings
from jlog.filesystem import ensure_daily_note, get_daily_note_filename, get_daily_note_path, replace_text_atomically
from jlog.templates import render_daily_note


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


def test_ensure_daily_note_creates_nested_daily_directory(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path, daily_folder=Path("Journal/Daily"))
    day = date(2026, 8, 12)

    note_path = ensure_daily_note(settings, day)

    assert note_path.parent == tmp_path / "Journal" / "Daily"
    assert note_path.parent.is_dir()


def test_ensure_daily_note_creates_note(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 12)

    note_path = ensure_daily_note(settings, day)

    assert note_path.is_file()


def test_ensure_daily_note_writes_rendered_template(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 12)

    note_path = ensure_daily_note(settings, day)

    assert note_path.read_text(encoding="utf-8") == render_daily_note(day)


def test_ensure_daily_note_does_not_overwrite_existing_note(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 12)

    note_path = get_daily_note_path(settings, day)
    note_path.parent.mkdir(parents=True)

    existing_content = "This existing journal entry must survive.\n"
    note_path.write_text(existing_content, encoding="utf-8")

    result = ensure_daily_note(settings, day)

    assert result == note_path
    assert result.read_text(encoding="utf-8") == existing_content


def test_ensure_daily_note_is_idempotent(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 12)

    note_path = ensure_daily_note(settings, day)

    updated_content = note_path.read_text(encoding="utf-8") + "\nUser-added journal content.\n"
    note_path.write_text(updated_content, encoding="utf-8")

    second_path = ensure_daily_note(settings, day)

    assert second_path == note_path
    assert second_path.read_text(encoding="utf-8") == updated_content


def test_replace_text_atomically_replaces_existing_contents(tmp_path: Path) -> None:
    path = tmp_path / "note.md"
    path.write_text("original\n", encoding="utf-8")

    replace_text_atomically(path, "replacement\n")

    assert path.read_text(encoding="utf-8") == "replacement\n"


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not portable to Windows")
def test_replace_text_atomically_preserves_permissions(tmp_path: Path) -> None:
    path = tmp_path / "note.md"
    path.write_text("original\n", encoding="utf-8")
    path.chmod(0o640)

    replace_text_atomically(path, "replacement\n")

    assert stat.S_IMODE(path.stat().st_mode) == 0o640
