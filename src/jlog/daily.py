"""
Orchestration of operations on daily journal notes.
"""

from datetime import date, time
from pathlib import Path

from jlog.config import Settings
from jlog.filesystem import get_daily_note_path, replace_text_atomically
from jlog.frontmatter import (
    extract_frontmatter,
    parse_frontmatter_yaml,
    rebuild_document,
    require_daily_note,
    require_frontmatter_mapping,
    set_frontmatter_alias,
    set_frontmatter_rating,
    validate_known_frontmatter,
)
from jlog.markdown import format_log_entry, insert_log_entry


class _Unset:
    """
    Sentinel representing a value that was not supplied.
    """


_UNSET = (
    _Unset()
)  # Cleaner than using a plain object() because object is such a broad type that static narrowing becomes less useful.


def update_daily_note(
    settings: Settings, day: date, *, alias: str | None | _Unset = _UNSET, rating: int | None | _Unset = _UNSET
) -> Path:
    """
    Update user-editable frontmatter fields in an existing daily note.
    """

    note_path = get_daily_note_path(settings, day)

    with note_path.open(
        mode="r", encoding="utf-8", newline=""
    ) as file:  # newline="" is to ensure markdown body using CRLF or LF doesn't get accidentally converted.
        document = file.read()

    block = extract_frontmatter(document)
    parsed = parse_frontmatter_yaml(block.yaml)
    frontmatter = require_frontmatter_mapping(parsed)

    validated = validate_known_frontmatter(frontmatter)
    require_daily_note(validated, expected_date=day)

    if not isinstance(alias, _Unset):
        set_frontmatter_alias(frontmatter, alias)

    if not isinstance(rating, _Unset):
        set_frontmatter_rating(frontmatter, rating)

    updated_document = rebuild_document(block, frontmatter)

    if updated_document != document:
        replace_text_atomically(note_path, updated_document)

    return note_path


def append_daily_log(settings: Settings, day: date, timestamp: time, message: str) -> Path:
    """
    Append a timestamped log entry to an existing daily note.
    """

    entry = format_log_entry(timestamp, message)

    note_path = get_daily_note_path(settings, day)

    with note_path.open(mode="r", encoding="utf-8", newline="") as file:
        document = file.read()

    block = extract_frontmatter(document)
    parsed = parse_frontmatter_yaml(block.yaml)
    frontmatter = require_frontmatter_mapping(parsed)

    validated = validate_known_frontmatter(frontmatter)
    require_daily_note(validated, expected_date=day)

    updated_body = insert_log_entry(block.body, entry)

    body_start = len(document) - len(block.body)

    updated_document = document[:body_start] + updated_body

    replace_text_atomically(note_path, updated_document)

    return note_path
