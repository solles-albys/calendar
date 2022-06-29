from datetime import datetime, timedelta
from typing import Optional

from asyncpg import Connection

from lib.api.models.events import RCreateEvent, Event, Repetition, Participant, EDecision, ERepeatType
from lib.api.models.users import User
from lib.api.models.common import EDay
from lib.sql.user import get_one_user, get_users_from_event_rows
from lib.sql.participation import insert_many_participation
from lib.sql.const import PARTICIPATION_TABLE, EVENTS_TABLE, USERS_TABLE
from lib.util import repetitions


async def create_table_events(connection: Connection):
    await connection.execute(
        f'''
            CREATE TABLE IF NOT EXISTS {EVENTS_TABLE} (
                id                      serial CONSTRAINT {EVENTS_TABLE}_pk primary key,
                author                  varchar(255) CONSTRAINT event_author__fk references {USERS_TABLE}
                                            on update cascade on delete cascade,
                name                    text,
                description             text,
                start_time              timestamp,
                end_time                timestamp,
                repeat_type            varchar(100),
                repeat_weekly_days     varchar(100),
                repeat_monthly_last_week       bool,
                repeat_due_date        timestamp,
                repeat_each            int
            );
        '''
    )


async def insert_event(connection: Connection, request: RCreateEvent) -> Event:
    async with connection.transaction():
        base_event_id = await connection.fetchval(
            f'''
                INSERT INTO {EVENTS_TABLE} (
                    author,
                    name,
                    description,
                    start_time,
                    end_time,
                    repeat_type,
                    repeat_weekly_days,
                    repeat_monthly_last_week,
                    repeat_due_date,
                    repeat_each
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                )
                RETURNING id;
            ''',
            request.author_login,
            request.name,
            request.description,
            request.start_time.replace(tzinfo=None),
            request.end_time.replace(tzinfo=None),
            request.repetition.type.value if request.repetition else None,
            ','.join(request.repetition.weekly_days) if request.repetition else '',
            request.repetition.monthly_last_week if request.repetition else None,
            request.repetition.due_date.replace(tzinfo=None) if request.repetition and request.repetition.due_date else None,
            request.repetition.each if request.repetition else None
        )

        event = Event(
            id=base_event_id,
            author=await get_one_user(connection, request.author_login),
            start_time=request.start_time.replace(tzinfo=None),
            end_time=request.end_time.replace(tzinfo=None),
            name=request.name,
            description=request.description,
            participants=request.participants,
            repetition=request.repetition,
        )

        # if request.notifications:
        # TODO

        if request.participants:
            await insert_many_participation(connection, base_event_id, request.participants)

        return event


async def get_one_event(connection: Connection, event_id: int) -> Optional[Event]:
    result = await connection.fetch(f'''
        SELECT * FROM {EVENTS_TABLE} e
        LEFT OUTER JOIN {PARTICIPATION_TABLE} p on e.id = p.event_id
        WHERE e.id = $1
    ''', event_id)

    if not result:
        return None

    # TODO: fetch notifications

    users: dict[str, User] = await get_users_from_event_rows(connection, result)

    event_row = result[0]
    event = Event(
        id=event_row['id'],
        author=users[event_row['author']],
        name=event_row['name'],
        description=event_row['description'] or '',
        start_time=event_row['start_time'],
        end_time=event_row['end_time'],
    )

    for row in result:
        if row['user_login']:
            event.participants.append(
                Participant(
                    user=users[row['user_login']],  # TODO: fetch user in one request,
                    decision=EDecision(row['decision']),
                )
            )

    return event


def is_event_in_interval(event: Event, time_from: datetime, time_to: datetime):
    return event.start_time < time_to and event.end_time > time_from


def extend_with_repeats(result: list[Event], time_from: datetime, time_to: datetime) -> bool:
    if not result:
        return False

    base_event = result[-1]
    if not is_event_in_interval(base_event, time_from, time_to):
        result.pop(-1)

    if base_event.repetition is None:
        return False

    repeat_until = time_to
    if base_event.repetition.due_date is not None:
        repeat_until = min(time_to, base_event.repetition.due_date)

    repeat_dates = repetitions.iterate_repetitions(
        repetition=base_event.repetition,
        event_start_date=base_event.start_time,
        repeat_start_date=time_from,
        repeat_end_date=repeat_until
    )

    if not repeat_dates:
        return False

    duration = base_event.end_time - base_event.start_time

    for date in repeat_dates:
        # do not need to deepcopy, no future usage of mutable fields not supposed to happen
        new_event = base_event.copy(deep=False)
        new_event.start_time = date
        new_event.end_time = date + duration
        result.append(new_event)

    return True


async def get_many_users_events(connection: Connection, logins: set[str], time_from: datetime, time_to: datetime) -> list[Event]:
    # TODO: fix условие вхождения
    response = await connection.fetch(
        f'''
            SELECT * FROM {EVENTS_TABLE} e
            LEFT OUTER JOIN {PARTICIPATION_TABLE} p on e.id = p.event_id
            WHERE (p.user_login = ANY($1::text[]) OR e.author = ANY($1::text[])) AND
                  (
                      (e.end_time > $2 AND e.start_time < $3) OR
                      (e.repeat_type is not NULL AND (e.repeat_due_date is NULL OR e.repeat_due_date >= $2))
                  );
        ''',
        logins, time_from.replace(tzinfo=None), time_to.replace(tzinfo=None)
    )

    if not response:
        return []

    users: dict[str, User] = await get_users_from_event_rows(connection, response)

    result: list[Event] = []
    last_is_repeat = False
    for row in response:
        if not result or result[-1].id != row['id']:
            if len(result) > 0:
                was_extended = extend_with_repeats(result, time_from, time_to)
                if not was_extended:
                    last_is_repeat = last_is_repeat
                else:
                    last_is_repeat = True

            event = Event(
                id=row['id'],
                author=users[row['author']],
                name=row['name'],
                description=row['description'],
                start_time=row['start_time'],
                end_time=row['end_time'],
            )

            if row['repeat_type'] is not None:
                weekly_days = []
                for v in row['repeat_weekly_days'].split(','):
                    if v:
                        weekly_days.append(EDay(v))

                event.repetition = Repetition(
                    type=ERepeatType(row['repeat_type']),
                    weekly_days=weekly_days,
                    monthly_last_week=row['repeat_monthly_last_week'],
                    due_date=row['repeat_due_date'],
                    each=row['repeat_each']
                )

            result.append(event)

        if row['user_login']:
            result[-1].participants.append(
                Participant(
                    user=users[row['user_login']],
                    decision=EDecision(row['decision']),
                )
            )

    if not last_is_repeat:
        extend_with_repeats(result, time_from, time_to)

    return sorted(result, key=lambda e: e.start_time)


async def get_user_events(connection: Connection, login: str, time_from: datetime, time_to: datetime):
    return await get_many_users_events(connection, {login,}, time_from, time_to)
