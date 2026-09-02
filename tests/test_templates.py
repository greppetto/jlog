from datetime import date

from jlog.templates import render_daily_note


def test_render_daily_note() -> None:
    result = render_daily_note(date(2026, 8, 12))

    expected = """\
---
id: 20260812
date: 2026-08-12
type: daily
alias:
rating:
banner: WednesdayBanner.gif
cssclasses:
  - wednesday
  - daily
journal: daily
journal_date: 2026-08-12
journal_start_date: 2026-08-12
journal_end_date: 2026-08-12
---
# 2026-08-12-Wednesday

## Logs

## End of day

### What mattered today?

### Tomorrow
"""

    assert result == expected


def test_render_daily_note_is_deterministic() -> None:
    day = date(2026, 8, 12)

    first = render_daily_note(day)
    second = render_daily_note(day)

    assert first == second


def test_render_daily_note_ends_with_one_newline() -> None:
    result = render_daily_note(date(2026, 8, 12))

    assert result.endswith("\n")
    assert not result.endswith("\n\n")
