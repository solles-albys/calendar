from datetime import datetime, timedelta
from typing import Optional

from asyncpg import Connection

from lib.api.models.events import RCreateEvent, Event, Repetition, Participant, EDecision
from lib.api.models.users import User
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
                repeate_from_id         integer CONSTRAINT event_base__fk references {EVENTS_TABLE}
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
                    end_time
                ) VALUES (
                    $1, $2, $3, $4, $5
                )
                RETURNING id;
            ''',
            request.author_login,
            request.name,
            request.description,
            request.start_time.replace(tzinfo=None),
            request.end_time.replace(tzinfo=None),
        )

        event = Event(
            id=base_event_id,
            author=await get_one_user(connection, request.author_login),
            start_time=request.start_time.replace(tzinfo=None),
            end_time=request.end_time.replace(tzinfo=None),
            name=request.name,
            description=request.description,
            participants=request.participants,
        )

        if request.repetition:
            await _create_repetitions(connection, request.repetition, base_event=event)

        # if request.notifications:
        # TODO

        if request.participants:
            repeates_ids = await connection.fetch(f'''
                SELECT id FROM {EVENTS_TABLE} where repeate_from_id = $1;
            ''', event.id)

            event_ids = [event.id, *(r['id'] for r in repeates_ids)]
            await insert_many_participation(connection, event_ids, request.participants)

        return event


async def _create_repetitions(
        connection: Connection, repetition: Repetition, base_event: Event
):
    args: list[tuple] = []

    end_date = repetition.due_date or datetime.now() + timedelta(days=300)
    duration = base_event.end_time - base_event.start_time

    for start_date in repetitions.iterate_repetitions(repetition, base_event.start_time, end_date):
        args.append(
            (base_event.author.name, base_event.description, start_date, start_date + duration, base_event.id)
        )

    await connection.executemany(
        f'''
            INSERT INTO {EVENTS_TABLE} (
                author,
                name,
                description,
                start_time,
                end_time,
                repeate_from_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6
            );
        ''',
        args,
    )


async def get_one_event(connection: Connection, event_id: int) -> Optional[Event]:
    result = await connection.fetch(f'''
        SELECT * FROM {EVENTS_TABLE} e
        RIGHT OUTER JOIN {PARTICIPATION_TABLE} p on e.id = p.event_id || e.repeate_from_id = p.event_id
        WHERE e.id = $1
    ''', event_id)

    if not result:
        return None

    # TODO: fetch notifications

    users: dict[str, User] = get_users_from_event_rows(connection, result)

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
        event.participants.append(
            Participant(
                user=users[row['user_login']],  # TODO: fetch user in one request,
                decision=EDecision(row['accept_type']),
            )
        )

    return event


async def get_user_events(connection: Connection, user_login: str) -> list[Event]:
    response = await connection.fetch(f'''
        SELECT * FROM {EVENTS_TABLE} e
        RIGHT OUTER JOIN {PARTICIPATION_TABLE} p on e.id = p.event_id || e.repeate_from_id = p.event_id
        WHERE p.user_login = $1 or e.author = $1;
    ''', user_login)

    users: dict[str, User] = get_users_from_event_rows(connection, response)

    result: list[Event] = []
    for row in response:
        if not result or result[-1].id != row['id']:
            result.append(Event(
                id=row['id'],
                author=users[row['author']],
                name=row['name'],
                description=row['description'],
                start_time=row['start_time'],
                end_time=row['end_time'],
            ))

        result[-1].participants.append(
            Participant(
                user=users[row['user_login']],
                decision=EDecision(row['accept_type']),
            )
        )

    return result
