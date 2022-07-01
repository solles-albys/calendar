import asyncio
from datetime import datetime, timedelta

import pytest
from dateutil.relativedelta import relativedelta

from lib.api.events import create_event
from lib.api.users import create_user
from lib.models.events import RCreateEvent, Repetition, ERepeatType, Notification, EChannel
from lib.models.users import UserFull, Name
from lib.modules.notificator import Notificator
from tests.full_wait import full_wait_pending

TEST_USER = UserFull(login='test', name=Name(first='vova', last='last'))


@pytest.mark.asyncio
@full_wait_pending
async def test_notificator(db):
    await create_user(TEST_USER)

    now = datetime.now()

    event_start_time = now + timedelta(minutes=15, seconds=1)
    simple_event = RCreateEvent(
        author_login=TEST_USER.login,
        start_time=event_start_time,
        end_time=now + timedelta(days=60, hours=1),
        name='ВВВ',
        description='Hello',
        notifications=[
            Notification(channel=EChannel.email, offset='15m'),
        ],
    )
    simple = await create_event(simple_event)
    assert simple.notifications

    complex_event = RCreateEvent(
        author_login=TEST_USER.login,
        start_time=event_start_time,
        end_time=now + timedelta(days=60, hours=1),
        name='AAA',
        description='Hello',
        notifications=[
            Notification(channel=EChannel.telegram, offset='15m'),
        ],
        repetition=Repetition(
            type=ERepeatType.yearly,
            each=2,
            due_date=now + relativedelta(years=8) + timedelta(hours=16)
        ),
    )
    complex = await create_event(complex_event)
    assert complex.notifications

    notificator = Notificator(None)
    logs = []

    async def send_notification(notification):
        logs.append(
            f'notification: to {notification.recipient} '
            f'via {notification.channel} about event {notification.event_id}'
        )

    notificator.send_notification = send_notification

    await asyncio.sleep(1)
    async with db.connect() as connection:
        await notificator.run_once(connection)

    assert len(logs) == 2
