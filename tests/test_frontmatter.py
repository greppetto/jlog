"""
Tests for YAML frontmatter handling.
"""

from datetime import date

import pytest
from ruamel.yaml.comments import CommentedMap

from jlog.frontmatter import (
    FrontmatterError,
    extract_frontmatter,
    parse_frontmatter_yaml,
    rebuild_document,
    require_daily_note,
    require_frontmatter_mapping,
    set_frontmatter_alias,
    set_frontmatter_rating,
    validate_known_frontmatter,
)


def test_extract_frontmatter() -> None:
    document = """\
---
date: 2026-08-18
rating: 3
---
# 2026-08-18

## Logs

- Something happened.
"""

    block = extract_frontmatter(document)

    assert block.yaml == "date: 2026-08-18\nrating: 3\n"
    assert block.body == "# 2026-08-18\n\n## Logs\n\n- Something happened.\n"


def test_extract_frontmatter_rejects_missing_opening_delimiter() -> None:
    document = "# 2026-08-18\n"

    with pytest.raises(FrontmatterError):
        extract_frontmatter(document)


def test_extract_frontmatter_rejects_missing_closing_delimiter() -> None:
    document = """\
---
date: 2026-08-18
"""

    with pytest.raises(FrontmatterError):
        extract_frontmatter(document)


def test_parse_frontmatter_yaml_rejects_invalid_yaml() -> None:
    yaml_text = """\
date: 2026-08-18
invalid: [
"""

    with pytest.raises(FrontmatterError):
        parse_frontmatter_yaml(yaml_text)


def test_require_frontmatter_mapping_accepts_mapping() -> None:
    parsed = parse_frontmatter_yaml("date: 2026-08-18\n")

    result = require_frontmatter_mapping(parsed)

    assert isinstance(result, CommentedMap)


def test_require_frontmatter_mapping_rejects_sequence() -> None:
    parsed = parse_frontmatter_yaml("- first\n- second\n")

    with pytest.raises(FrontmatterError):
        require_frontmatter_mapping(parsed)


def test_require_frontmatter_mapping_rejects_empty_yaml() -> None:
    parsed = parse_frontmatter_yaml("")

    with pytest.raises(FrontmatterError):
        require_frontmatter_mapping(parsed)


def test_validate_known_frontmatter_ignores_unknown_fields() -> None:
    parsed = parse_frontmatter_yaml(
        """\
date: 2026-08-18
type: daily
rating: 3
journal: daily
weather: rainy
"""
    )
    mapping = require_frontmatter_mapping(parsed)

    validated = validate_known_frontmatter(mapping)

    assert validated.date == date(2026, 8, 18)
    assert validated.rating == 3
    assert mapping["weather"] == "rainy"


def test_validate_known_frontmatter_rejects_invalid_rating() -> None:
    parsed = parse_frontmatter_yaml(
        """\
date: 2026-08-18
type: daily
rating: 99
journal: daily
"""
    )
    mapping = require_frontmatter_mapping(parsed)

    with pytest.raises(FrontmatterError):
        validate_known_frontmatter(mapping)


@pytest.mark.parametrize(
    "yaml_text",
    [
        "type: daily\njournal: daily\n",
        "date: 2026-08-18\njournal: daily\n",
        "date: 2026-08-18\ntype: daily\n",
    ],
)
def test_require_daily_note_rejects_missing_required_metadata(yaml_text: str) -> None:
    parsed = parse_frontmatter_yaml(yaml_text)
    mapping = require_frontmatter_mapping(parsed)
    validated = validate_known_frontmatter(mapping)

    with pytest.raises(FrontmatterError):
        require_daily_note(
            validated,
            expected_date=date(2026, 8, 18),
        )


def test_require_daily_note_rejects_date_mismatch() -> None:
    parsed = parse_frontmatter_yaml(
        """\
date: 2026-08-17
type: daily
journal: daily
"""
    )
    mapping = require_frontmatter_mapping(parsed)
    validated = validate_known_frontmatter(mapping)

    with pytest.raises(FrontmatterError):
        require_daily_note(
            validated,
            expected_date=date(2026, 8, 18),
        )


def test_set_frontmatter_rating() -> None:
    parsed = parse_frontmatter_yaml("rating: 3\n")
    mapping = require_frontmatter_mapping(parsed)

    set_frontmatter_rating(mapping, 4)

    assert mapping["rating"] == 4


def test_set_frontmatter_rating_rejects_invalid_value_without_mutating() -> None:
    parsed = parse_frontmatter_yaml("rating: 3\n")
    mapping = require_frontmatter_mapping(parsed)

    with pytest.raises(FrontmatterError):
        set_frontmatter_rating(mapping, 99)

    assert mapping["rating"] == 3


def test_set_frontmatter_alias_normalizes_value() -> None:
    parsed = parse_frontmatter_yaml("alias:\n")
    mapping = require_frontmatter_mapping(parsed)

    set_frontmatter_alias(mapping, "  Parser day  ")

    assert mapping["alias"] == "Parser day"


def test_set_frontmatter_alias_normalizes_blank_value_to_none() -> None:
    parsed = parse_frontmatter_yaml("alias: Existing\n")
    mapping = require_frontmatter_mapping(parsed)

    set_frontmatter_alias(mapping, "   ")

    assert mapping["alias"] is None


def test_rebuild_document_preserves_unmodified_frontmatter_and_body() -> None:
    document = """\
---
date: 2026-08-18
type: daily
alias: "A strange day"
rating: 3  # tentative
journal: daily
weather: rainy
---
# 2026-08-18

## Logs

- Existing entry. #idea
"""

    block = extract_frontmatter(document)
    parsed = parse_frontmatter_yaml(block.yaml)
    mapping = require_frontmatter_mapping(parsed)

    set_frontmatter_rating(mapping, 4)

    rebuilt = rebuild_document(block, mapping)

    assert 'alias: "A strange day"' in rebuilt
    assert "rating: 4  # tentative" in rebuilt
    assert "weather: rainy" in rebuilt

    rebuilt_block = extract_frontmatter(rebuilt)
    assert rebuilt_block.body == block.body
