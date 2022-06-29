import datetime

import pytest
from fastapi import HTTPException
from lib.api.methods.users import create_user, get_user_events
from lib.api.methods.events import create_event
from lib.api.models.users import UserFull, Name
from lib.api.models.events import Event, RCreateEvent, Repetition, Participant, ERepeatType
from lib.api.models.common import EDay
from lib.sql.const import USERS_TABLE
from tests.full_wait import full_wait_pending
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta


TEST_USER = UserFull(login='test', name=Name(first='vova', last='last'))
OTHER_USER = UserFull(login='other', name=Name(first='danya', last='ya'))
NOT_VALID_USER = UserFull(login='', name=Name(first='vova', last='last'))


SIMPLE_EVENT_REQ = RCreateEvent(
    author_login=TEST_USER.login,
    start_time=datetime(2022, 6, 26, 15),
    end_time=datetime(2022, 6, 26, 16),
    name='Test Simple Event',
    description='no repeats, just one event'
)


@pytest.mark.asyncio
@full_wait_pending
async def test_create_user(db):
    result = await create_user(TEST_USER)
    assert result is None

    result = await create_user(TEST_USER)
    assert isinstance(result, HTTPException)

    result = await create_user(NOT_VALID_USER)
    assert isinstance(result, HTTPException)

    async with db.connect() as conn:
        response = await conn.fetch(f'SELECT * FROM {USERS_TABLE};')

    assert len(response) == 1
    assert response[0]['login'] == 'test'


@pytest.mark.asyncio
@full_wait_pending
async def test_get_user_events_simple(db):
    await create_user(TEST_USER)
    await create_user(OTHER_USER)

    event = SIMPLE_EVENT_REQ.copy(deep=True)
    await create_event(event)

    event = SIMPLE_EVENT_REQ.copy(deep=True)
    event.participants.append(
        Participant(user=OTHER_USER)
    )
    await create_event(event)

    test_user_events = await get_user_events(
        TEST_USER.login,
        SIMPLE_EVENT_REQ.start_time - timedelta(days=1),
        SIMPLE_EVENT_REQ.end_time + timedelta(days=1)
    )
    assert len(test_user_events) == 2

    test_other_events = await get_user_events(
        OTHER_USER.login,
        SIMPLE_EVENT_REQ.start_time - timedelta(days=1),
        SIMPLE_EVENT_REQ.end_time + timedelta(days=1)
    )
    assert len(test_other_events) == 1


@pytest.mark.asyncio
@full_wait_pending
async def test_get_user_events_daily_repeated(db):
    await create_user(TEST_USER)

    event = SIMPLE_EVENT_REQ.copy(deep=True)
    event.repetition = Repetition(
        type=ERepeatType.daily,
        each=3,
        due_date=datetime(2022, 7, 10)
    )  # 6.29, 7.2, 7.5, 7.8
    await create_event(event)

    events = await get_user_events(TEST_USER.login, datetime(2022, 7, 11), datetime(2022, 7, 18))
    assert not events

    events = await get_user_events(TEST_USER.login, datetime(2022, 7, 1), datetime(2022, 7, 4))
    assert len(events) == 1
    assert events[0].start_time == datetime(2022, 7, 2, 15)
    assert events[0].end_time == datetime(2022, 7, 2, 16)

    events = await get_user_events(TEST_USER.login, datetime(2022, 6, 30), datetime(2022, 7, 10))
    assert len(events) == 3
    assert events[0].start_time == datetime(2022, 7, 2, 15)
    assert events[0].end_time == datetime(2022, 7, 2, 16)


@pytest.mark.asyncio
@full_wait_pending
async def test_get_user_events_weekly_repeated(db):
    await create_user(TEST_USER)

    event = SIMPLE_EVENT_REQ.copy(deep=True)
    event.repetition = Repetition(
        type=ERepeatType.weakly,
        each=2,
        due_date=datetime(2022, 7, 26)
    )  # 26.6, 10.7, 24.7

    await create_event(event)

    events = await get_user_events(TEST_USER.login, datetime(2022, 7, 25), datetime(2022, 8, 25))
    assert not events

    events = await get_user_events(TEST_USER.login, datetime(2022, 7, 9), datetime(2022, 7, 25))
    assert len(events) == 2
    assert events[0].start_time == datetime(2022, 7, 10, 15)


@pytest.mark.asyncio
@full_wait_pending
async def test_get_user_events_weekly_days_repeated(db):
    await create_user(TEST_USER)

    event = SIMPLE_EVENT_REQ.copy(deep=True)
    event.repetition = Repetition(
        type=ERepeatType.weakly,
        each=2,
        weekly_days=[EDay.wed, EDay.sun],
        due_date=datetime(2022, 7, 11)
    )  # 26.6, 6.7, 10.7
    await create_event(event)

    events = await get_user_events(TEST_USER.login, datetime(2022, 6, 20), datetime(2022, 6, 25))
    assert not events

    events = await get_user_events(TEST_USER.login, datetime(2022, 6, 20), datetime(2022, 7, 12))
    assert len(events) == 3
    assert events[0].start_time == event.start_time

    events = await get_user_events(TEST_USER.login, datetime(2022, 6, 28), datetime(2022, 7, 12))
    assert len(events) == 2
    assert events[0].start_time == datetime(2022, 7, 6, 15)


@pytest.mark.asyncio
@full_wait_pending
async def test_get_user_events_monthly_number(db):
    await create_user(TEST_USER)

    event = SIMPLE_EVENT_REQ.copy(deep=True)
    event.repetition = Repetition(
        type=ERepeatType.monthly_number,
        each=2,
        due_date=datetime(2022, 6, 26) + relativedelta(months=8)
    )
    await create_event(event)

    events = await get_user_events(TEST_USER.login, datetime(2022, 7, 27), datetime(2023, 7, 27))
    assert len(events) == 3
    assert events[0].start_time == datetime(2022, 8, 26, 15)


@pytest.mark.asyncio
@full_wait_pending
async def test_get_user_events_monthly_last_week(db):
    await create_user(TEST_USER)

    event = SIMPLE_EVENT_REQ.copy(deep=True)
    event.repetition = Repetition(
        type=ERepeatType.monthly_day_weekno,
        monthly_last_week=True,
        each=2,
        due_date=datetime(2022, 6, 26) + relativedelta(months=6)
    )  # 26.6, 28.8, 30.10, 25.12
    await create_event(event)

    events = await get_user_events(TEST_USER.login, datetime(2022, 7, 27), datetime(2023, 7, 27))
    assert len(events) == 3
    assert events[0].start_time == datetime(2022, 8, 28, 15)


@pytest.mark.asyncio
@full_wait_pending
async def test_get_user_events_monthly_week_number(db):
    await create_user(TEST_USER)

    event = SIMPLE_EVENT_REQ.copy(deep=True)
    event.repetition = Repetition(
        type=ERepeatType.monthly_day_weekno,
        each=2,
        due_date=datetime(2022, 6, 26) + relativedelta(months=6)
    )  # 26.6, 28.8, 23.10, 25.12
    await create_event(event)

    events = await get_user_events(TEST_USER.login, datetime(2022, 7, 27), datetime(2023, 7, 27))
    assert len(events) == 3
    assert events[0].start_time == datetime(2022, 8, 28, 15)
    assert events[1].start_time == datetime(2022, 10, 23, 15)


@pytest.mark.asyncio
@full_wait_pending
async def test_get_user_events_yearly(db):
    await create_user(TEST_USER)

    event = SIMPLE_EVENT_REQ.copy(deep=True)
    event.repetition = Repetition(
        type=ERepeatType.yearly,
        each=2,
        due_date=datetime(2022, 6, 26) + relativedelta(years=6) + timedelta(hours=16)
    )  # 26.6.2022, 26.6.2024, 26.6.2026, 26.6.2028
    await create_event(event)

    events = await get_user_events(TEST_USER.login, datetime(2022, 7, 27), datetime(2030, 7, 27))
    assert len(events) == 3
    assert events[0].start_time == datetime(2024, 6, 26, 15)
