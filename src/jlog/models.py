"""
Pydantic models used by jlog.
"""

from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from jlog.utils import get_weekday_name


class Frontmatter(BaseModel):
    """
    Metadata for a daily journal note.
    """

    date: Date
    type: Literal["daily"] = "daily"
    alias: str | None = None
    rating: int | None = Field(default=None, ge=1, le=10)
    journal: Literal["daily"] = "daily"

    @field_validator("alias")
    @classmethod
    def normalize_alias(cls, value: str | None) -> str | None:
        """
        Normalize an optional day alias.
        """

        if value is None:
            return None

        value = value.strip()
        return value or None

    @computed_field
    @property
    def id(self) -> int:
        """
        Return the date-derived daily note identifier.
        """

        return self.date.year * 10_000 + self.date.month * 100 + self.date.day

    @computed_field
    @property
    def banner(self) -> str:
        """
        Return the banner filename corresponding to the weekday.
        """

        return f"{get_weekday_name(self.date)}Banner.gif"

    @computed_field
    @property
    def cssclasses(self) -> list[str]:
        """
        Return the CSS classes for the daily note.
        """

        return [get_weekday_name(self.date).lower(), "daily"]

    @computed_field
    @property
    def journal_date(self) -> Date:
        """
        Return the journal date.
        """

        return self.date

    @computed_field
    @property
    def journal_start_date(self) -> Date:
        """
        Return the start date of this daily journal period.
        """

        return self.date

    @computed_field
    @property
    def journal_end_date(self) -> Date:
        """
        Return the end date of this daily journal period.
        """

        return self.date


class ExistingFrontmatter(BaseModel):
    """
    Validated jlog metadata read from existing frontmatter.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    date: Date | None = None
    type: Literal["daily"] | None = None
    alias: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    journal: Literal["daily"] | None = None

    @field_validator("alias")
    @classmethod
    def normalize_alias(cls, value: str | None) -> str | None:
        """
        Normalize an optional day alias.
        """

        if value is None:
            return None

        value = value.strip()
        return value or None
