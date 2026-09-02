from datetime import date
from pathlib import Path

import pytest

from jlog.config import Settings
from jlog.daily import update_daily_note
from jlog.filesystem import ensure_daily_note, get_daily_note_path
from jlog.frontmatter import (
    FrontmatterError,
    extract_frontmatter,
    parse_frontmatter_yaml,
    require_frontmatter_mapping,
)


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
