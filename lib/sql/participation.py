from asyncpg import Connection

from lib.api.models.events import Participant, EDecision
from lib.sql.const import USERS_TABLE, EVENTS_TABLE, PARTICIPATION_TABLE


async def create_table_participation(connection: Connection):
    await connection.execute(
        f'''
            CREATE TABLE IF NOT EXISTS {PARTICIPATION_TABLE}
            (
                user_login  varchar(255)
                    constraint user_participation__fk
                        references {USERS_TABLE}
                        on update cascade on delete cascade,
                event_id    int
                    constraint event_participation__fk
                        references {EVENTS_TABLE}
                        on update cascade on delete cascade,
                decision varchar(10),
                PRIMARY KEY (user_login, event_id)
            );
        '''
    )


async def insert_many_participation(connection: Connection, event_id: int, participants: list[Participant]):
    await connection.executemany(
        f'''
            INSERT INTO {PARTICIPATION_TABLE} (
                event_id,
                user_login,
                decision
            ) VALUES ($1, $2, $3);
        ''',
        (
            (event_id, participant.user.login, participant.decision.value)
            for participant in participants
        )
    )


async def accept_participation(connection: Connection, event_id: int, user_login: str, decision: EDecision):
    await connection.execute(
        f'''
            UPDATE {PARTICIPATION_TABLE} SET {{
                decision = $1
            }} WHERE (
                (event_id = $2 OR event_id = (SELECT repeate_from_id from {EVENTS_TABLE} WHERE id = event_id)) 
                AND user_login = $3;
        ''',
        decision.value, event_id, user_login
    )
