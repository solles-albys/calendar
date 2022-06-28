from datetime import datetime, timedelta
from typing import Optional, Generator
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


def set_start_date_due_to_interval(
    repetition: Repetition,
    event_start_date: datetime,
    repeat_start_date: datetime,
    repeat_end_date: datetime,
) -> Optional[datetime]:
    start_date = event_start_date

    if event_start_date > repeat_end_date or event_start_date > repetition.due_date:
        return None

    if event_start_date >= repeat_start_date:
        return start_date

    if repetition.type == ERepeatType.daily:
        if event_start_date + timedelta(days=repetition.each) > repeat_end_date:
            return None

        start_at_repeat_count = abs((repeat_start_date - event_start_date).days) // repetition.each
        result = start_date + timedelta(days=start_at_repeat_count * repetition.each)
        while result < repeat_start_date:
            result += timedelta(days=repetition.each)

        return result if result <= repeat_end_date else None

    elif repetition.type == ERepeatType.weakly:
        if repetition.weekly_days:
            result = event_start_date + timedelta(weeks=repetition.each - 1, days=1)
            inc = create_weekly_increment(repetition.each)
            while result < repeat_start_date or EDay.from_datetime(result) not in repetition.weekly_days:
                result = inc(result)

            return result if result <= repeat_end_date else None
        else:
            result = event_start_date + timedelta(weeks=repetition.each)
            while result < repeat_start_date:
                result += timedelta(weeks=repetition.each)

            return result if result <= repeat_end_date else None

    elif repetition.type == ERepeatType.monthly_number:
        result = event_start_date + relativedelta(months=+repetition.each)
        while result < repeat_start_date:
            result += relativedelta(months=+repetition.each)

        return result if result <= repeat_end_date else None

    elif repetition.type == ERepeatType.monthly_day_weekno:
        if repetition.monthly_last_week:
            result = event_start_date + relativedelta(months=repetition.each, day=31, weekday=weekday(start_date.weekday())(-1))
            if result > repeat_end_date:
                return None

            while result < event_start_date:
                result += relativedelta(months=repetition.each, day=31, weekday=weekday(start_date.weekday())(-1))

            return result if result <= repeat_end_date else None
        else:
            week_no = date.week_of_month(start_date)
            result = date.get_next_month_exact_week_day(start_date, week_no, repetition.each)
            if result > repeat_end_date:
                return None

            while result < event_start_date:
                result = date.get_next_month_exact_week_day(result, week_no, repetition.each)

            return result if result <= repeat_end_date else None

    elif repetition.type == ERepeatType.yearly:
        result = event_start_date + relativedelta(years=+repetition.each)
        if result > repeat_end_date:
            return None

        while result < repeat_start_date:
            result += relativedelta(years=+repetition.each)

        return result if result <= repeat_end_date else None

    elif repetition.type == ERepeatType.workday:
        result = repeat_start_date
        while result.weekday() not in (0, 1, 2, 3, 4):
            result += timedelta(days=1)

        return result if result <= repeat_end_date else None


def iterate_repetitions(
    repetition: Repetition,
    event_start_date: datetime,
    repeat_start_date: datetime,
    repeat_end_date: datetime,
) -> datetime:
    should_create = lambda d: True
    start_date = set_start_date_due_to_interval(
        repetition,
        event_start_date,
        repeat_start_date,
        repeat_end_date
    )

    if start_date is None:
        return

    if start_date > event_start_date:
        yield start_date

    if start_date > repetition.due_date:
        return

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
            increment = lambda d: d + relativedelta(months=repetition.each, day=31, weekday=weekday(event_start_date.weekday())(-1))
        else:
            week_no = date.week_of_month(event_start_date)
            increment = lambda d: date.get_next_month_exact_week_day(d, week_no, repetition.each)
    elif repetition.type == ERepeatType.yearly:
        increment = lambda d: d + relativedelta(years=+repetition.each)
    elif repetition.type == ERepeatType.workday:
        increment = lambda d: d + relativedelta(days=1)
        should_create = lambda d: d.weekday() in range(5)
    else:
        raise ValueError('Unknown repetition type')

    next_date = increment(start_date)
    while next_date <= repeat_end_date:
        if next_date < repeat_start_date:
            continue

        if not should_create(next_date):
            next_date = increment(next_date)
            continue

        yield next_date

        next_date = increment(next_date)
