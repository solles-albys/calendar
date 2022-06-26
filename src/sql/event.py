from src.api.models import EventCreateRequest, Event, User, Participant, EAcceptType, ERepeat
from src.sql.const import PARTICIPATION_TABLE, EVENTS_TABLE, USERS_TABLE
from src.sql import participation as participation_sql

from asyncpg import Connection
from typing import Optional


async def create_table(connection: Connection):
    await connection.execute(
        f'''
            CREATE TABLE IF NOT EXISTS {EVENTS_TABLE} (
                id              serial CONSTRAINT {EVENTS_TABLE}_pk primary key,
                author          varchar(255) CONSTRAINT event_author__fk references {USERS_TABLE}
                                on update cascade on delete cascade,
                name            text,
                description     text,
                start_time      timestamp,
                end_time        timestamp,
                repeat_type    varchar(50)
            );
        '''
    )


async def insert(connection: Connection, event: EventCreateRequest) -> Event:
    async with connection.transaction():
        event_id = await connection.fetchval(
            f'''
                INSERT INTO {EVENTS_TABLE} (
                    name, 
                    author,
                    description, 
                    start_time, 
                    end_time, 
                    repeat_type
                ) VALUES (
                    $1, $2, $3, $4, $5, $6
                )
                RETURNING id;
            ''',
            event.name,
            event.author,
            event.description,
            event.start_time.replace(tzinfo=None),
            event.end_time.replace(tzinfo=None),
            str(event.repeat_type) if event.repeat_type else None
        )

        if event.participants:
            await participation_sql.insert_many(connection, event_id, event.participants)

    return Event(
        id=event_id,
        author=User(login=event.author),
        start_time=event.start_time,
        end_time=event.end_time,
        name=event.name,
        description=event.description,
        repeat_type=event.repeat_type,
        participants=event.participants,
    )


async def get_one(connection: Connection, event_id: int) -> Optional[Event]:
    result = await connection.fetch(f'''
        SELECT * FROM {EVENTS_TABLE} e
        RIGHT OUTER JOIN {PARTICIPATION_TABLE} p on e.id = p.event_id 
        WHERE e.id = $1
    ''', event_id)

    if not result:
        return None

    event_row = result[0]
    event = Event(
        id=event_row['id'],
        author=User(login=event_row['author']),
        name=event_row['name'],
        description=event_row['description'] or '',
        start_time=event_row['start_time'],
        end_time=event_row['end_time'],
        repeat_type=ERepeat(event_row['repeat_type']) if event_row['repeat_type'] else None,
    )

    for row in result:
        event.participants.append(Participant(
            user=User(login=row['user_login']),
            accept=EAcceptType(row['accept_type'])
        ))

    return event
