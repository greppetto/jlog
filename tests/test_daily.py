from datetime import date, time
from pathlib import Path

import pytest

from jlog.config import Settings
from jlog.daily import append_daily_log, update_daily_note
from jlog.filesystem import ensure_daily_note, get_daily_note_path
from jlog.frontmatter import (
    FrontmatterError,
    extract_frontmatter,
    parse_frontmatter_yaml,
    require_frontmatter_mapping,
)
from jlog.markdown import MarkdownError


def test_update_daily_note_updates_rating(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 18)

    note_path = ensure_daily_note(settings, day)

    result = update_daily_note(settings, day, rating=4)

    assert result == note_path

    document = note_path.read_text(encoding="utf-8")
    block = extract_frontmatter(document)
    parsed = parse_frontmatter_yaml(block.yaml)
    mapping = require_frontmatter_mapping(parsed)

    assert mapping["rating"] == 4


def test_update_daily_note_updates_alias_and_rating(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 18)

    note_path = ensure_daily_note(settings, day)

    update_daily_note(settings, day, alias="Parser day", rating=5)

    document = note_path.read_text(encoding="utf-8")
    block = extract_frontmatter(document)
    parsed = parse_frontmatter_yaml(block.yaml)
    mapping = require_frontmatter_mapping(parsed)

    assert mapping["alias"] == "Parser day"
    assert mapping["rating"] == 5


def test_update_daily_note_preserves_unknown_frontmatter_and_body(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 18)
    note_path = get_daily_note_path(settings, day)

    note_path.parent.mkdir(parents=True)

    document = """\
---
date: 2026-08-18
type: daily
alias: "A strange day"
rating: 3  # tentative
journal: daily
weather: rainy
custom_property: keep-me
---
# 2026-08-18

## Logs

- Existing thought. #idea
- Existing progress. #progress

## End of day
"""

    note_path.write_text(document, encoding="utf-8")

    original_body = extract_frontmatter(document).body

    update_daily_note(settings, day, rating=4)

    updated_document = note_path.read_text(encoding="utf-8")
    updated_block = extract_frontmatter(updated_document)

    assert updated_block.body == original_body
    assert "weather: rainy" in updated_block.yaml
    assert "custom_property: keep-me" in updated_block.yaml
    assert 'alias: "A strange day"' in updated_block.yaml
    assert "rating: 4  # tentative" in updated_block.yaml


def test_update_daily_note_invalid_rating_leaves_file_unchanged(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 18)

    note_path = ensure_daily_note(settings, day)
    original = note_path.read_bytes()

    with pytest.raises(FrontmatterError):
        update_daily_note(settings, day, rating=99)

    assert note_path.read_bytes() == original


def test_update_daily_note_invalid_existing_frontmatter_leaves_file_unchanged(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 18)
    note_path = get_daily_note_path(settings, day)

    note_path.parent.mkdir(parents=True)

    document = """\
---
date: 2026-08-18
type: weekly
rating: 3
journal: daily
---
# Important existing content
"""

    note_path.write_text(document, encoding="utf-8")
    original = note_path.read_bytes()

    with pytest.raises(FrontmatterError):
        update_daily_note(settings, day, rating=4)

    assert note_path.read_bytes() == original


def test_update_daily_note_date_mismatch_leaves_file_unchanged(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    expected_day = date(2026, 8, 18)
    note_path = get_daily_note_path(settings, expected_day)

    note_path.parent.mkdir(parents=True)

    document = """\
---
date: 2026-08-17
type: daily
rating: 3
journal: daily
---
# Existing content
"""

    note_path.write_text(document, encoding="utf-8")
    original = note_path.read_bytes()

    with pytest.raises(FrontmatterError):
        update_daily_note(settings, expected_day, rating=4)

    assert note_path.read_bytes() == original


def test_update_daily_note_can_clear_alias(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 8, 18)

    note_path = ensure_daily_note(settings, day)

    update_daily_note(settings, day, alias="Parser day")

    update_daily_note(settings, day, alias=None)

    document = note_path.read_text(encoding="utf-8")
    block = extract_frontmatter(document)
    parsed = parse_frontmatter_yaml(block.yaml)
    mapping = require_frontmatter_mapping(parsed)

    assert mapping["alias"] is None


def test_append_daily_log(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 9, 15)

    note_path = ensure_daily_note(settings, day)

    result = append_daily_log(settings, day, time(18, 18), "Implemented log insertion. #progress")

    assert result == note_path

    document = note_path.read_text(encoding="utf-8")

    assert "- 18:18 Implemented log insertion. #progress" in document


def test_append_daily_log_preserves_existing_entries(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 9, 15)

    note_path = ensure_daily_note(settings, day)

    append_daily_log(settings, day, time(9, 0), "First entry.")

    append_daily_log(settings, day, time(10, 30), "Second entry.")

    document = note_path.read_text(encoding="utf-8")

    assert "- 09:00 First entry." in document
    assert "- 10:30 Second entry." in document

    assert document.index("- 09:00 First entry.") < document.index("- 10:30 Second entry.")


def test_append_daily_log_preserves_frontmatter(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 9, 15)

    note_path = ensure_daily_note(settings, day)

    before = note_path.read_text(encoding="utf-8")
    original_frontmatter = extract_frontmatter(before).yaml

    append_daily_log(settings, day, time(10, 0), "New entry.")

    after = note_path.read_text(encoding="utf-8")

    assert extract_frontmatter(after).yaml == original_frontmatter


def test_append_daily_log_missing_logs_section_leaves_file_unchanged(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 9, 15)
    note_path = get_daily_note_path(settings, day)

    note_path.parent.mkdir(parents=True)

    document = """\
---
date: 2026-09-15
type: daily
journal: daily
---
# 2026-09-15

## End of day
"""

    note_path.write_text(document, encoding="utf-8")
    original = note_path.read_bytes()

    with pytest.raises(MarkdownError):
        append_daily_log(settings, day, time(10, 0), "This must not be written.")

    assert note_path.read_bytes() == original


def test_append_daily_log_invalid_message_leaves_file_unchanged(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 9, 15)

    note_path = ensure_daily_note(settings, day)
    original = note_path.read_bytes()

    with pytest.raises(MarkdownError):
        append_daily_log(settings, day, time(10, 0), "First line\nSecond line")

    assert note_path.read_bytes() == original


def test_append_daily_log_ignores_logs_text_in_frontmatter(tmp_path: Path) -> None:
    settings = Settings(vault_path=tmp_path)
    day = date(2026, 9, 15)
    note_path = get_daily_note_path(settings, day)

    note_path.parent.mkdir(parents=True)

    document = """\
---
date: 2026-09-15
type: daily
journal: daily
custom_property: "## Logs"
---
# 2026-09-15

## Logs

## End of day
"""

    note_path.write_text(document, encoding="utf-8")

    append_daily_log(settings, day, time(10, 0), "Actual log entry.")

    updated = note_path.read_text(encoding="utf-8")

    assert 'custom_property: "## Logs"' in updated
    assert "- 10:00 Actual log entry." in updated
