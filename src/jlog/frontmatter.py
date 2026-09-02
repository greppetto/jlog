"""
Reading and manipulating YAML frontmatter by jlog.
"""

from dataclasses import dataclass
from datetime import date
from io import StringIO
from typing import cast

from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import YAMLError

from jlog.exceptions import FrontmatterError
from jlog.models import ExistingFrontmatter


@dataclass(frozen=True, slots=True)
class FrontmatterBlock:
    """
    The frontmatter and markdown body extracted from a document.
    """

    yaml: str
    body: str


def extract_frontmatter(document: str) -> FrontmatterBlock:
    """
    Extract YAML frontmatter and the markdown body from a document.

    Frontmatter must begin on the first line and be enclosed by lines containing exactly ``---``.
    """

    lines = document.splitlines(keepends=True)

    if not lines or lines[0].rstrip("\r\n") != "---":
        raise FrontmatterError("Document does not begin with frontmatter.")

    closing_index: int | None = None

    for index, line in enumerate(lines[1:], start=1):
        if line.rstrip("\r\n") == "---":
            closing_index = index
            break

    if closing_index is None:
        raise FrontmatterError("Frontmatter has no closing delimiter.")

    yaml_text = "".join(lines[1:closing_index])
    body = "".join(lines[closing_index + 1 :])

    return FrontmatterBlock(yaml=yaml_text, body=body)


def parse_frontmatter_yaml(yaml_text: str) -> object:
    """
    Parse YAML frontmatter while preserving round-trip information.
    """

    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True

    try:
        return cast(object, yaml.load(yaml_text))  # pyright: ignore[reportUnknownMemberType]
    except YAMLError as exc:
        raise FrontmatterError("Frontmatter contains invalid YAML.") from exc


def require_frontmatter_mapping(data: object) -> CommentedMap:
    """
    Validate that parsed frontmatter is a YAML mapping.
    """

    if not isinstance(data, CommentedMap):
        raise FrontmatterError("Frontmatter must be a YAML mapping.")

    return data


def validate_known_frontmatter(frontmatter: CommentedMap) -> ExistingFrontmatter:
    """
    Validate the subset of existing frontmatter understood by jlog.
    """

    try:
        return ExistingFrontmatter.model_validate(frontmatter)
    except ValidationError as exc:
        raise FrontmatterError("Frontmatter contains invalid jlog metadata.") from exc


def require_daily_note(frontmatter: ExistingFrontmatter, expected_date: date) -> None:
    """
    Validate that frontmatter identifies the expected daily note.
    """

    if frontmatter.date is None:
        raise FrontmatterError("Daily note frontmatter is missing 'date'.")

    if frontmatter.type is None:
        raise FrontmatterError("Daily note frontmatter is missing 'type'.")

    if frontmatter.journal is None:
        raise FrontmatterError("Daily note frontmatter is missing 'journal'.")

    if frontmatter.date != expected_date:
        raise FrontmatterError(
            "Daily note frontmatter date does not match the expected date. "
            f"{frontmatter.date.isoformat()} does not match "
            f"expected date {expected_date.isoformat()}."
        )


def set_frontmatter_alias(frontmatter: CommentedMap, alias: str | None) -> None:
    """
    Validate and set the alias in existing frontmatter.
    """

    try:
        validated = ExistingFrontmatter.model_validate({"alias": alias})
    except ValidationError as exc:
        raise FrontmatterError("Invalid daily note alias.") from exc

    frontmatter["alias"] = validated.alias


def set_frontmatter_rating(frontmatter: CommentedMap, rating: int | None) -> None:
    """
    Validate and set the rating in existing frontmatter.
    """

    try:
        validated = ExistingFrontmatter.model_validate({"rating": rating})
    except ValidationError as exc:
        raise FrontmatterError("Invalid daily note rating.") from exc

    frontmatter["rating"] = validated.rating


def serialize_frontmatter_yaml(frontmatter: CommentedMap) -> str:
    """
    Serialize existing frontmatter while preserving round-trip metadata.
    """

    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True

    stream = StringIO()
    yaml.dump(frontmatter, stream)  # pyright: ignore[reportUnknownMemberType]

    return stream.getvalue()


def rebuild_document(block: FrontmatterBlock, frontmatter: CommentedMap) -> str:
    """
    Rebuild a markdown document with updated frontmatter.
    """

    yaml_text = serialize_frontmatter_yaml(frontmatter)

    return f"---\n{yaml_text}---\n{block.body}"
