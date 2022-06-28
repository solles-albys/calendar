import pytest
from lib.api.models.events import Repetition, ERepeatType
from lib.api.models.common import EDay
from lib.util.date import _get_next_month_num
from lib.util.repetitions import iterate_repetitions
from datetime import datetime, timedelta
from itertools import chain
from dateutil.relativedelta import relativedelta

START_DATE = datetime(2022, 6, 26, 15, 0, 0)  # 26.06.2022 15:00


def test_daily_repetition():
    repetition = Repetition(
        type=ERepeatType.daily,
        each=1,
        due_date=START_DATE + timedelta(days=7),
    )

    result = list(iterate_repetitions(
        repetition=repetition,
        event_start_date=START_DATE,
        repeat_start_date=START_DATE - timedelta(days=1),
        repeat_end_date=repetition.due_date
    ))

    assert len(result) == 7
    assert result == [
        START_DATE + timedelta(days=i)
        for i in range(1, 8, 1)
    ]

    repetition = Repetition(
        type=ERepeatType.daily,
        each=4,
        due_date=START_DATE + timedelta(days=7*4),
    )
    result = list(iterate_repetitions(
        repetition=repetition,
        event_start_date=START_DATE,
        repeat_start_date=START_DATE - timedelta(days=1),
        repeat_end_date=repetition.due_date
    ))
    assert len(result) == 7
    assert result == [
        START_DATE + timedelta(days=i*4)
        for i in range(1, 8, 1)
    ]


def test_weakly_repetition():
    repetition = Repetition(
        type=ERepeatType.weakly,
        each=1,
        due_date=START_DATE + timedelta(weeks=7)
    )

    result = list(iterate_repetitions(
        repetition=repetition,
        event_start_date=START_DATE,
        repeat_start_date=START_DATE - timedelta(days=1),
        repeat_end_date=repetition.due_date
    ))

    assert len(result) == 7
    assert result == [
        START_DATE + timedelta(weeks=i)
        for i in range(1, 8, 1)
    ]

    repetition = Repetition(
        type=ERepeatType.weakly,
        each=3,
        due_date=START_DATE + timedelta(weeks=7*3)
    )
    result = list(iterate_repetitions(
        repetition=repetition,
        event_start_date=START_DATE,
        repeat_start_date=START_DATE - timedelta(days=1),
        repeat_end_date=repetition.due_date
    ))

    assert len(result) == 7
    assert result == [
        START_DATE + timedelta(weeks=i*3)
        for i in range(1, 8, 1)
    ]

    repetition = Repetition(
        type=ERepeatType.weakly,
        each=2,
        weekly_days=[EDay.mon, EDay.fri],
        due_date=START_DATE + timedelta(weeks=2 * 2)
    )
    result = list(iterate_repetitions(
        repetition=repetition,
        event_start_date=START_DATE,
        repeat_start_date=START_DATE - timedelta(days=1),
        repeat_end_date=repetition.due_date
    ))

    assert len(result) == 4
    date_mon = START_DATE - timedelta(days=6)
    date_fri = START_DATE - timedelta(days=2)
    assert result == list(chain.from_iterable(
        [
            (date_mon + timedelta(weeks=i*2), date_fri + timedelta(weeks=i*2),)
            for i in range(1, 3, 1)
        ]
    ))


def test_monthly_number_repetition():
    repetition = Repetition(
        type=ERepeatType.monthly_number,
        each=2,
        due_date=START_DATE + relativedelta(months=8)
    )

    result = list(iterate_repetitions(
        repetition=repetition,
        event_start_date=START_DATE,
        repeat_start_date=START_DATE - timedelta(days=1),
        repeat_end_date=repetition.due_date
    ))

    assert len(result) == 4
    assert result == [
        START_DATE.replace(year=_get_next_month_num(START_DATE, i*2)[0], month=_get_next_month_num(START_DATE, i*2)[1])
        for i in range(1, 5, 1)
    ]


def test_monthly_day_weekno_repetition():
    repetition = Repetition(
        type=ERepeatType.monthly_day_weekno,
        each=2,
        due_date=START_DATE + relativedelta(months=8)
    )

    result = list(iterate_repetitions(
        repetition=repetition,
        event_start_date=START_DATE,
        repeat_start_date=START_DATE - timedelta(days=1),
        repeat_end_date=repetition.due_date
    ))

    assert len(result) == 4
    assert result == [
        START_DATE.replace(month=8, day=28),
        START_DATE.replace(month=10, day=23),
        START_DATE.replace(month=12, day=25),
        START_DATE.replace(year=2023, month=2, day=26)
    ]

    repetition = Repetition(
        type=ERepeatType.monthly_day_weekno,
        each=2,
        monthly_last_week=True,
        due_date=START_DATE + relativedelta(months=8)
    )
    result = list(iterate_repetitions(
        repetition=repetition,
        event_start_date=START_DATE,
        repeat_start_date=START_DATE - timedelta(days=1),
        repeat_end_date=repetition.due_date
    ))

    assert len(result) == 4
    assert result == [
        START_DATE.replace(month=8, day=28),
        START_DATE.replace(month=10, day=30),
        START_DATE.replace(month=12, day=25),
        START_DATE.replace(year=2023, month=2, day=26)
    ]


def test_yearly_repetition():
    repetition = Repetition(
        type=ERepeatType.yearly,
        each=2,
        due_date=START_DATE + relativedelta(years=8)
    )
    result = list(iterate_repetitions(
        repetition=repetition,
        event_start_date=START_DATE,
        repeat_start_date=START_DATE - timedelta(days=1),
        repeat_end_date=repetition.due_date
    ))

    assert len(result) == 4
    assert result == [
        START_DATE + relativedelta(years=2*i)
        for i in range(1, 5, 1)
    ]


def test_workday_repetition():
    repetition = Repetition(
        type=ERepeatType.workday,
        due_date=START_DATE + timedelta(weeks=2)
    )

    result = list(iterate_repetitions(
        repetition=repetition,
        event_start_date=START_DATE,
        repeat_start_date=START_DATE - timedelta(days=1),
        repeat_end_date=repetition.due_date
    ))

    assert len(result) == 10
    assert result == [
        START_DATE + timedelta(days=i)
        for i in range(1, 13, 1)
        if (START_DATE + timedelta(days=i)).weekday() in (0, 1, 2, 3, 4)
    ]
