"""
Markdown template generation for jlog.
"""

from datetime import date
from io import StringIO

from ruamel.yaml import YAML

from jlog.models import Frontmatter
from jlog.utils import get_weekday_name


def ignore_yaml_aliases(_: object) -> bool:
    return True


def serialize_frontmatter(frontmatter: Frontmatter) -> str:
    """
    Serialize frontmatter to YAML in jlog's canonical field order.
    """

    data = {
        "id": frontmatter.id,
        "date": frontmatter.date,
        "type": frontmatter.type,
        "alias": frontmatter.alias,
        "rating": frontmatter.rating,
        "banner": frontmatter.banner,
        "cssclasses": frontmatter.cssclasses,
        "journal": frontmatter.journal,
        "journal_date": frontmatter.journal_date,
        "journal_start_date": frontmatter.journal_start_date,
        "journal_end_date": frontmatter.journal_end_date,
    }

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.representer.ignore_aliases = ignore_yaml_aliases

    stream = StringIO()
    yaml.dump(data, stream)  # pyright: ignore[reportUnknownMemberType]

    return stream.getvalue()


def render_daily_note(day: date) -> str:
    """
    Render a complete daily journal note for a calendar date.
    """

    frontmatter = Frontmatter(date=day)
    frontmatter_text = serialize_frontmatter(frontmatter)

    return (
        "---\n"
        f"{frontmatter_text}"
        "---\n"
        "\n"
        f"# {day.isoformat()}-{get_weekday_name(day)}\n"
        "\n"
        "## Logs\n"
        "\n"
        "## End of day\n"
        "\n"
        "### What mattered today?\n"
        "\n"
        "### Tomorrow\n"
    )


print(render_daily_note(date(2026, 8, 12)))
