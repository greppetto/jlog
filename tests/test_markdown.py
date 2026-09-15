"""
Tests for Markdown maniplation.
"""

from datetime import time

import pytest

from jlog.markdown import (
    MarkdownError,
    find_logs_section,
    format_log_entry,
    get_heading_level,
    insert_log_entry,
    is_logs_heading,
)


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("## Logs", True),
        ("## Logs\n", True),
        ("## Logs\r\n", True),
        (" ## Logs", False),
        ("## Logs ", False),
        ("### Logs", False),
        ("## logs", False),
        ("## Logs from yesterday", False),
    ],
)
def test_is_logs_heading(line: str, expected: bool) -> None:
    assert is_logs_heading(line) is expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("# Heading", 1),
        ("## Heading", 2),
        ("### Heading", 3),
        ("#### Heading", 4),
        ("##### Heading", 5),
        ("###### Heading", 6),
        ("#\n", 1),
        ("###Not a heading", None),
        ("####### Heading", None),
        ("ordinary text", None),
    ],
)
def test_get_heading_level(line: str, expected: int | None) -> None:
    assert get_heading_level(line) == expected


def test_find_logs_section() -> None:
    document = """\
# 2026-09-15

## Logs

- 09:00 First entry.

## End of day
"""

    section = find_logs_section(document)

    assert section.heading_index == 2
    assert section.content_start_index == 3
    assert section.end_index == 6


def test_find_logs_section_does_not_end_at_nested_heading() -> None:
    document = """\
## Logs

- 09:00 First entry.

### Related thought

Some text.

## End of day
"""

    section = find_logs_section(document)

    lines = document.splitlines(keepends=True)

    assert lines[section.end_index].rstrip("\n") == "## End of day"


def test_find_logs_section_rejects_missing_section() -> None:
    document = """\
# 2026-09-15

## End of day
"""

    with pytest.raises(MarkdownError):
        find_logs_section(document)


def test_find_logs_section_rejects_multiple_sections() -> None:
    document = """\
## Logs

- First.

## Logs

- Second.
"""

    with pytest.raises(MarkdownError):
        find_logs_section(document)


def test_format_log_entry() -> None:
    result = format_log_entry(time(9, 5), "Finished the parser. #progress")

    assert result == "- 09:05 Finished the parser. #progress"


def test_format_log_entry_strips_surrounding_whitespace() -> None:
    result = format_log_entry(time(15, 43), "  Learned something. #idea  ")

    assert result == "- 15:43 Learned something. #idea"


@pytest.mark.parametrize(
    "message",
    [
        "",
        " ",
        "   ",
    ],
)
def test_format_log_entry_rejects_empty_message(message: str) -> None:
    with pytest.raises(MarkdownError):
        format_log_entry(time(10, 0), message)


@pytest.mark.parametrize(
    "message",
    [
        "First line\nSecond line",
        "First line\r\nSecond line",
        "Message with trailing newline\n",
    ],
)
def test_format_log_entry_rejects_multiline_message(message: str) -> None:
    with pytest.raises(MarkdownError):
        format_log_entry(time(10, 0), message)


def test_insert_log_entry_into_empty_logs_section() -> None:
    document = """\
# 2026-09-15

## Logs

## End of day

### What mattered today?

### Tomorrow
"""

    result = insert_log_entry(document, "- 10:22 First entry.")

    expected = """\
# 2026-09-15

## Logs

- 10:22 First entry.

## End of day

### What mattered today?

### Tomorrow
"""

    assert result == expected


def test_insert_log_entry_appends_after_existing_entry() -> None:
    document = """\
## Logs

- 09:00 First entry.

## End of day
"""

    result = insert_log_entry(document, "- 10:22 Second entry.")

    expected = """\
## Logs

- 09:00 First entry.
- 10:22 Second entry.

## End of day
"""

    assert result == expected


def test_insert_log_entry_appends_after_multiple_entries() -> None:
    document = """\
## Logs

- 09:00 First.
- 10:00 Second.
- 11:00 Third.

## End of day
"""

    result = insert_log_entry(document, "- 12:00 Fourth.")

    expected = """\
## Logs

- 09:00 First.
- 10:00 Second.
- 11:00 Third.
- 12:00 Fourth.

## End of day
"""

    assert result == expected


def test_insert_log_entry_when_logs_is_final_section() -> None:
    document = """\
## Logs

- 09:00 First entry.
"""

    result = insert_log_entry(document, "- 10:00 Second entry.")

    expected = """\
## Logs

- 09:00 First entry.
- 10:00 Second entry.
"""

    assert result == expected


def test_insert_log_entry_after_nested_content() -> None:
    document = """\
## Logs

- 09:00 First entry.

### Related thought

Some detail.

## End of day
"""

    result = insert_log_entry(document, "- 10:00 Second entry.")

    expected = """\
## Logs

- 09:00 First entry.

### Related thought

Some detail.
- 10:00 Second entry.

## End of day
"""

    assert result == expected


def test_insert_log_entry_adds_separator_before_next_section() -> None:
    document = """\
## Logs

- 09:00 First entry.
## End of day
"""

    result = insert_log_entry(document, "- 10:00 Second entry.")

    expected = """\
## Logs

- 09:00 First entry.
- 10:00 Second entry.

## End of day
"""

    assert result == expected


def test_insert_log_entry_preserves_crlf() -> None:
    document = "## Logs\r\n\r\n- 09:00 First entry.\r\n\r\n## End of day\r\n"

    result = insert_log_entry(document, "- 10:00 Second entry.")

    expected = "## Logs\r\n\r\n- 09:00 First entry.\r\n- 10:00 Second entry.\r\n\r\n## End of day\r\n"

    assert result == expected
