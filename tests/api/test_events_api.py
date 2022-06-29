import pytest
from tests.full_wait import full_wait_pending

from lib.api.methods.events import create_event, accept_event_by_user, get_event
from lib.api.methods.users import create_user
from lib.api.models.events import RCreateEvent, Event, Repetition, ERepeatType, EDecision, Participant
from lib.api.models.common import EDay
from lib.api.models.users import UserFull, Name, User
from lib.sql.event import get_one_event
from datetime import datetime

TEST_USER = UserFull(login='test', name=Name(first='vova', last='last'))
TEST_USER_TWO = UserFull(login='test_two', name=Name(first='vova', last='last'))

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
