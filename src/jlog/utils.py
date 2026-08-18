from datetime import date

WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def get_weekday_name(day: date) -> str:
    """
    Return the English weekday name for a calendar date.
    """

    return WEEKDAYS[day.weekday()]
