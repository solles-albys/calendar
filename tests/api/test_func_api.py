import pytest
from tests.full_wait import full_wait_pending

from lib.models.users import UserFull, Name
from lib.api.users import create_user
from lib.api.events import create_event
from lib.api.funcs import calculate_free_slot
from lib.models.funcs import RCalcFreeTime
from lib.models.events import RCreateEvent
from datetime import datetime, timedelta

USER_ONE = UserFull(login='one', name=Name(first='one', last='one'))
USER_TWO = UserFull(login='two', name=Name(first='two', last='two'))
USER_THREE = UserFull(login='three', name=Name(first='three', last='three'))

EVENTS = (
    (  # one
        USER_ONE.login,
        ((datetime(2022, 6, 26, 15), timedelta(hours=1)),  # to 16:00
         (datetime(2022, 6, 26, 16), timedelta(hours=2, minutes=30)),  # to 18:30
         (datetime(2022, 6, 26, 18, 30), timedelta(hours=1)),  # to 19:30
         # free time 19:30 - 21:30
         (datetime(2022, 6, 26, 21, 30), timedelta(hours=1, minutes=30)),  # to 23:00
         # free time 23:30 - 00:30
         (datetime(2022, 6, 27, 0, 30), timedelta(hours=2)))  # to 2:30
    ),
    (
        USER_TWO.login,
        ((datetime(2022, 6, 26, 16, 20), timedelta(minutes=20)),  # to 16:40
         # free_time 16:40 - 19:10
         (datetime(2022, 6, 26, 19, 10), timedelta(hours=3, minutes=20)),  # to 22:30
         # free_time 22:30 - 22:50
         (datetime(2022, 6, 26, 22, 50), timedelta(minutes=40)))  # to 23:30
    ),
    (
        USER_THREE.login,
        ((datetime(2022, 6, 27, 1, 30), timedelta(hours=5)),)  # to 6:30
    )
)


@pytest.mark.asyncio
@full_wait_pending
async def test_calc_users_free_time(db):
    await create_user(USER_ONE)
    await create_user(USER_TWO)
    await create_user(USER_THREE)

    for login, times in EVENTS:
        for start_time, duration in times:
            await create_event(RCreateEvent(
                author_login=login,
                start_time=start_time,
                end_time=start_time + duration,
                name=f'{login} Встречка',
                description='Я занят, не звонить!',
            ))

    request = RCalcFreeTime(
        event_duration=timedelta(hours=1),
        user_logins={USER_ONE.login, USER_TWO.login, USER_THREE.login},
        start_calc_from=datetime(2022, 6, 26, 16),
    )

    result = await calculate_free_slot(request)
    assert result.start == datetime(2022, 6, 26, 23, 30)
    assert result.end == datetime(2022, 6, 27, 0, 30)

    request.start_calc_from = datetime(2022, 6, 26, 14)
    result = await calculate_free_slot(request)
    assert result.start == datetime(2022, 6, 26, 14)
    assert result.end == datetime(2022, 6, 26, 15)
