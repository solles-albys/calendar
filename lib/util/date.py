from datetime import datetime, timedelta
from lib.api.models.common import EDay
from math import ceil


def _get_next_month_num(current: datetime, inc=1) -> (int, int):
    year = current.year
    next_month = current.month + inc
    while next_month > 13:
        year += 1
        next_month -= 12

    return year, next_month


# def get_next_month_exact_day(current: datetime, each_month: int, day_num: int):
#     next_month_num = _get_next_month_num(current, inc=each_month)
#     next_month = current.replace(month=next_month_num)
#     last_day_month = current.replace(month=_get_next_month_num(next_month)) - timedelta(days=1)
#     if last_day_month.day < day_num:
#         return last_day_month
#
#     return next_month.replace(day=day_num)


def get_next_month_exact_week_day(current: datetime, week_no: int, inc=1) -> datetime:
    """Return day of exact weekday as current but in {week_no} week number of next month."""

    if 1 > week_no or week_no > 5:
        raise ValueError('Week number should be in interval [1..4]')

    next_year, next_month = _get_next_month_num(current, inc)
    first_day_month = current.replace(year=next_year, month=next_month, day=1)

    # Look for target weekday
    cur_week_no = 1
    while first_day_month.weekday() != current.weekday():
        first_day_month += timedelta(days=1)
        if first_day_month.weekday() == 0:
            cur_week_no += 1

    while cur_week_no < week_no:
        first_day_month += timedelta(weeks=1)
        cur_week_no += 1
        if first_day_month.month - current.month not in (inc, -12 + inc):
            # Exceed number of weeks, so return last weekday of that month
            return first_day_month - timedelta(weeks=1)

    return first_day_month


def week_of_month(dt: datetime) -> int:
    """Returns the week of the month for the specified date."""
    first_day = dt.replace(day=1)

    dom = dt.day
    adjusted_dom = dom + first_day.weekday()

    return int(ceil(adjusted_dom/7.0))
