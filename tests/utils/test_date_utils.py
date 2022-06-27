import pytest

from lib.util import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil._common import weekday


def test_get_month_last_week_day():
    current = datetime(2022, 6, 27)

    result = current + relativedelta(months=1, day=31, weekday=weekday(current.weekday())(-1))

    assert result.month - current.month in (1, -11)
    assert result.weekday() == current.weekday()
    assert result.day == 25


def test_get_next_month_exact_week_day():
    current = datetime(2022, 6, 27)
    result_week = date.get_next_month_exact_week_day(current, 1)

    assert result_week.day == 4
    assert result_week.month == 7

    result_week = date.get_next_month_exact_week_day(current, 2)
    assert result_week.day == 4
    assert result_week.month == 7

    result_week = date.get_next_month_exact_week_day(current, 3)
    assert result_week.day == 11
    assert result_week.month == 7

    result_week = date.get_next_month_exact_week_day(current, 4)
    assert result_week.day == 18
    assert result_week.month == 7


def test_week_of_month():
    dt = datetime(2022, 6, 27)
    assert date.week_of_month(dt) == 5

    dt = datetime(2022, 6, 6)
    assert date.week_of_month(dt) == 2
