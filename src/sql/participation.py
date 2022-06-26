from asyncpg import Connection
from src.api.models import Participant
from src.sql.const import USERS_TABLE, EVENTS_TABLE, PARTICIPATION_TABLE

_PARTICIPATION = 'participation'


async def create_table(connection: Connection):
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
                    accept_type varchar(50),
                    PRIMARY KEY (user_login, event_id)
                );
            '''
    )


async def insert_many(connection: Connection, event_id: int, participants: list[Participant]):
    await connection.executemany(
        f'''
                        INSERT INTO {PARTICIPATION_TABLE} (
                            event_id,
                            user_login,
                            accept_type
                        ) VALUES ($1, $2, $3);
                    ''',
        (
            (event_id, participant.user.login, participant.accept.value)
            for participant in participants
        )
    )

