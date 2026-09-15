"""
Markdown structure and manipulation for jlog.
"""

from dataclasses import dataclass
from datetime import time

from jlog.exceptions import MarkdownError

LOGS_HEADING = "## Logs"
LOGS_HEADING_LEVEL = 2


@dataclass(frozen=True, slots=True)
class LogsSection:
    """
    Line boundaries of the Logs section in a Markdown document.
    """

    heading_index: int
    content_start_index: int
    end_index: int


def is_logs_heading(line: str) -> bool:
    """
    Return whether a line is exactly the jlog Logs heading.
    """
    return line.rstrip("\r\n") == LOGS_HEADING


def get_heading_level(line: str) -> int | None:
    """
    Return the level of an ATX Markdown heading, if present.
    """

    content = line.rstrip("\r\n")

    level = 0

    for character in content:
        if character != "#":
            break
        level += 1

    if not 1 <= level <= 6:
        return None

    if len(content) == level:
        return level

    if content[level] not in (" ", "\t"):
        return None

    return level


def find_logs_section(document: str) -> LogsSection:
    """
    Locate the Logs section in a Markdown document.
    """

    lines = document.splitlines(keepends=True)

    logs_indices = [index for index, line in enumerate(lines) if is_logs_heading(line)]

    if not logs_indices:
        raise MarkdownError("Document has no '## Logs section.'")

    if len(logs_indices) > 1:
        raise MarkdownError("Document has multiple '## Logs' sections.")

    heading_index = logs_indices[0]
    end_index = len(lines)

    for index, line in enumerate(lines[heading_index + 1 :], start=heading_index + 1):
        heading_level = get_heading_level(line)

        if heading_level is not None and heading_level <= LOGS_HEADING_LEVEL:
            end_index = index
            break

    return LogsSection(
        heading_index=heading_index,
        content_start_index=heading_index + 1,
        end_index=end_index,
    )


def format_log_entry(timestamp: time, message: str) -> str:
    """
    Format a timestamp and message as a single journal log entry.
    """

    if "\n" in message or "\r" in message:
        raise MarkdownError("Log message must be a single line.")

    message = message.strip()

    if not message:
        raise MarkdownError("Log message must not be empty.")

    return f"- {timestamp.strftime('%H:%M')} {message}"


def _is_blank_line(line: str) -> bool:
    """
    Return whether a line contains only whitespace.
    """

    return not line.rstrip("\r\n").strip()


def _get_line_ending(line: str) -> str:
    """
    Return the line-ending sequence used by a line.
    """

    if line.endswith("\r\n"):
        return "\r\n"

    if line.endswith("\n"):
        return "\n"

    if line.endswith("\r"):
        return "\r"

    return "\n"


def insert_log_entry(document: str, entry: str) -> str:
    """
    Insert a formatted log entry at the end of the Logs section.
    """

    if "\n" in entry or "\r" in entry:
        raise MarkdownError("log entry must be a single line")

    if not entry:
        raise MarkdownError("log entry must not be empty")

    lines = document.splitlines(keepends=True)
    section = find_logs_section(document)

    line_ending = _get_line_ending(lines[section.heading_index])

    insertion_index = section.end_index

    while insertion_index > section.content_start_index and _is_blank_line(lines[insertion_index - 1]):
        insertion_index -= 1

    section_is_empty = insertion_index == section.content_start_index

    prefix = "".join(lines[:insertion_index])
    suffix = "".join(lines[insertion_index:])

    if not prefix.endswith(("\n", "\r")):
        prefix += line_ending

    if section_is_empty:
        prefix += line_ending

    insertion = entry + line_ending

    has_following_section = section.end_index < len(lines)
    has_trailing_blank_line = insertion_index < section.end_index

    if has_following_section and not has_trailing_blank_line:
        insertion += line_ending

    return prefix + insertion + suffix
