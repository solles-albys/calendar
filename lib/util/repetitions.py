from datetime import datetime, timedelta

from lib.api.models.common import EDay

from dateutil._common import weekday
from dateutil.relativedelta import relativedelta

from lib.api.models.events import ERepeatType, Repetition
from lib.util import date


def create_weekly_increment(each: int):

    def increment(d: datetime):
        if d.weekday() == 6 and each > 1:
            return d + timedelta(weeks=each) - timedelta(days=6)
        else:
            return d + timedelta(days=1)

    return increment


def iterate_repetitions(repetition: Repetition, start_date: datetime, end_date: datetime) -> datetime:
    should_create = lambda d: True

    if repetition.type == ERepeatType.daily:
        increment = lambda d: d + timedelta(days=repetition.each)
    elif repetition.type == ERepeatType.weakly:
        if repetition.weekly_days:
            increment = create_weekly_increment(repetition.each)
            should_create = lambda d: EDay.from_datetime(d) in repetition.weekly_days
        else:
            increment = lambda d: d + timedelta(weeks=repetition.each)
    elif repetition.type == ERepeatType.monthly_number:
        increment = lambda d: d + relativedelta(months=+repetition.each)
    elif repetition.type == ERepeatType.monthly_day_weekno:
        if repetition.monthly_last_week:
            increment = lambda d: d + relativedelta(months=repetition.each, day=31, weekday=weekday(start_date.weekday())(-1))
        else:
            week_no = date.week_of_month(start_date)
            increment = lambda d: date.get_next_month_exact_week_day(d, week_no, repetition.each)
    elif repetition.type == ERepeatType.yearly:
        increment = lambda d: d + relativedelta(years=+repetition.each)
    elif repetition.type == ERepeatType.workday:
        increment = lambda d: d + relativedelta(days=1)
        should_create = lambda d: d.weekday() in range(5)
    else:
        raise ValueError('Unknown repetition type')

    next_date = increment(start_date)
    while next_date <= end_date:
        if not should_create(next_date):
            next_date = increment(next_date)
            continue

        yield next_date

        next_date = increment(next_date)
