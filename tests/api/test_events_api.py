import pytest
from tests.full_wait import full_wait_pending

from lib.api.events import create_event, accept_event_by_user
from lib.api.users import create_user
from lib.models.events import RCreateEvent, Repetition, ERepeatType, EDecision, Participant, Notification, EChannel
from lib.models.common import EDay
from lib.sql.notifications import NotificationRecord
from lib.models.users import UserFull, Name, User
from lib.sql.event import get_one_event
from lib.sql.const import NOTIFICATION_TABLE, EVENTS_TABLE
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

TEST_USER = UserFull(login='test', name=Name(first='vova', last='last'))
TEST_USER_TWO = UserFull(login='test_two', name=Name(first='vova', last='last'))
TEST_USER_THREE = UserFull(login='test_three', name=Name(first='vova', last='last'))


@pytest.mark.asyncio
@full_wait_pending
async def test_create_simple_event(db):
    await create_user(TEST_USER)

    simple_event = RCreateEvent(
        author_login=TEST_USER.login,
        start_time=datetime(2022, 6, 26, 15),
        end_time=datetime(2022, 6, 26, 16),
        name='ВВВ',
        description='Hello'
    )

    event = await create_event(simple_event)
    assert event is not None

    async with db.connect(read_only=True) as connection:
        from_db = await get_one_event(connection, 1)

    assert from_db == event


@pytest.mark.asyncio
@full_wait_pending
async def test_create_complex_event(db):
    await create_user(TEST_USER)
    await create_user(TEST_USER_TWO)

    complex_event = RCreateEvent(
        author_login=TEST_USER.login,
        start_time=datetime(2022, 6, 26, 15),
        end_time=datetime(2022, 6, 26, 16),
        name='ВВВ',
        description='Hello',
        repetition=Repetition(
            type=ERepeatType.weakly,
            weekly_days=[EDay.mon, EDay.sun, EDay.wed],
            each=3
        ),
        participants=[Participant(
            user=User(
                login=TEST_USER_TWO.login,
                name=TEST_USER_TWO.name.copy()
            )
        )]
    )

    event = await create_event(complex_event)
    assert event is not None

    async with db.connect(read_only=True) as connection:
        from_db = await get_one_event(connection, 1)

    assert from_db.id == event.id
    assert from_db.author == event.author
    assert from_db.start_time == event.start_time
    assert from_db.end_time == event.end_time
    assert from_db.name == event.name
    assert from_db.description == event.description
    assert len(from_db.participants) == len(event.participants)


@pytest.mark.asyncio
@full_wait_pending
async def test_accept_event(db):
    await create_user(TEST_USER)
    await create_user(TEST_USER_TWO)

    complex_event = RCreateEvent(
        author_login=TEST_USER.login,
        start_time=datetime(2022, 6, 26, 15),
        end_time=datetime(2022, 6, 26, 16),
        name='ВВВ',
        description='Hello',
        repetition=Repetition(
            type=ERepeatType.weakly,
            weekly_days=[EDay.mon, EDay.sun, EDay.wed],
            each=3
        ),
        participants=[Participant(
            user=User(
                login=TEST_USER_TWO.login,
                name=TEST_USER_TWO.name.copy()
            )
        )]
    )

    event = await create_event(complex_event)
    assert event is not None

    await accept_event_by_user(1, TEST_USER_TWO.login, EDecision.yes)

    async with db.connect(read_only=True) as connection:
        from_db = await get_one_event(connection, 1)

    assert from_db.participants[0].decision == EDecision.yes


@pytest.mark.asyncio
@full_wait_pending
async def test_notifications(db):
    await create_user(TEST_USER)
    await create_user(TEST_USER_TWO)
    await create_user(TEST_USER_THREE)

    now = datetime.now()

    event_start_time = now + timedelta(days=60)
    simple_event = RCreateEvent(
        author_login=TEST_USER.login,
        start_time=event_start_time,
        end_time=now + timedelta(days=60, hours=1),
        name='ВВВ',
        description='Hello',
        notifications=[
            Notification(channel=EChannel.email, offset='30m'),
            Notification(channel=EChannel.telegram, offset='30d'),
            Notification(channel=EChannel.sms, offset='1h')
        ],
        participants=[
            Participant(user=User(
                login=TEST_USER_TWO.login,
                name=TEST_USER_TWO.name.copy()
            )),
            Participant(user=User(
                login=TEST_USER_THREE.login,
                name=TEST_USER_THREE.name.copy()
            ), decision=EDecision.no)
        ]
    )

    event = await create_event(simple_event)
    assert event.notifications

    async with db.connect() as connection:
        rows = await connection.fetch(
            f'''
                SELECT n.*, e.repeat_due_date, e.repeat_each, e.repeat_monthly_last_week, e.repeat_type, e.repeat_weekly_days
                FROM {NOTIFICATION_TABLE} n
                RIGHT JOIN {EVENTS_TABLE} e on e.id = n.event_id
            '''
        )

        records = [NotificationRecord.from_row(row) for row in rows]

    assert len(records) == 6

    for r in records:
        if r.recipient == TEST_USER.login:
            if r.channel == EChannel.email:
                assert r.next_notify_at == event_start_time - timedelta(minutes=30)
            elif r.channel == EChannel.telegram:
                assert r.next_notify_at == event_start_time - timedelta(days=30)
            elif r.channel == EChannel.sms:
                assert r.next_notify_at == event_start_time - timedelta(hours=1)


@pytest.mark.asyncio
@full_wait_pending
async def test_complex_notifications(db):
    await create_user(TEST_USER)
    await create_user(TEST_USER_TWO)
    await create_user(TEST_USER_THREE)

    complex_event = RCreateEvent(
        author_login=TEST_USER.login,
        start_time=datetime(2022, 6, 26, 15),
        end_time=datetime(2022, 6, 26, 16),
        name='ВВВ',
        description='Hello',
        repetition=Repetition(
            type=ERepeatType.yearly,
            each=2,
            due_date=datetime(2022, 6, 26) + relativedelta(years=8) + timedelta(hours=16)
        ),  # 26.6.2022, 26.6.2024, 26.6.2026, 26.6.2028, 26.6.2030
        participants=[Participant(
            user=User(
                login=TEST_USER_TWO.login,
                name=TEST_USER_TWO.name.copy()
            )
        )],
        notifications=[
            Notification(channel=EChannel.email, offset='30m'),
            Notification(channel=EChannel.telegram, offset='30d'),
            Notification(channel=EChannel.sms, offset='1h')
        ],
    )

    event_start_time = datetime(2022, 6, 26, 15)
    now = datetime.now()
    while event_start_time < now:
        event_start_time += relativedelta(years=2)

    assert event_start_time <= datetime(2030, 6, 26, 15)

    event = await create_event(complex_event)
    assert event.notifications

    async with db.connect() as connection:
        rows = await connection.fetch(
            f'''
                SELECT n.*, e.repeat_due_date, e.repeat_each, e.repeat_monthly_last_week, e.repeat_type, e.repeat_weekly_days
                FROM {NOTIFICATION_TABLE} n
                RIGHT JOIN {EVENTS_TABLE} e on e.id = n.event_id
            '''
        )

        records = [NotificationRecord.from_row(row) for row in rows]

    assert len(records) == 6

    for r in records:
        if r.recipient == TEST_USER.login:
            if r.channel == EChannel.email:
                assert r.next_notify_at == event_start_time - timedelta(minutes=30)
            elif r.channel == EChannel.telegram:
                assert r.next_notify_at == event_start_time - timedelta(days=30)
            elif r.channel == EChannel.sms:
                assert r.next_notify_at == event_start_time - timedelta(hours=1)
