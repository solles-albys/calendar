from lib.models.users import UserFull, User, Name
from lib.models.common import EDay, Time
from asyncpg import Connection
from lib.sql.const import USERS_TABLE
from typing import Union, Iterable, Optional


async def create_table_users(connection: Connection):
    await connection.execute(
        f'''CREATE TABLE IF NOT EXISTS {USERS_TABLE} (
            login           varchar(255) CONSTRAINT {USERS_TABLE}_pk primary key,
            first_name      varchar(255),
            last_name       varchar(255),
            work_day_from   varchar(3),
            work_day_to     varchar(3),
            work_time_from  varchar(5),
            work_time_to    varchar(5),
            
            session_id      varchar(255),
            last_seen       timestamp
        );'''
    )

    await connection.execute(
        f'''CREATE INDEX IF NOT EXISTS user_session_id__indx on {USERS_TABLE} (session_id);'''
    )


def user_row_to_model(row: dict, full: False):
    model = UserFull if full else User

    kwargs = {
        'login': row['login'],
        'name': Name(
            first=row['first_name'],
            last=row['last_name']
        )
    }

    if full and row['work_day_from']:
        kwargs['work_day_from'] = EDay(row['work_day_from'])
        kwargs['work_day_to'] = EDay(row['work_day_to'])
        kwargs['work_time_from'] = Time.from_str(row['work_time_from'])
        kwargs['work_time_to'] = Time.from_str(row['work_time_to'])

    return model(**kwargs)


async def insert_user(connection: Connection, user: UserFull) -> UserFull:
    time_kwargs = (None, None, None, None)
    if user.work_days is not None:
        time_kwargs = (
            user.work_days.day_from,
            user.work_days.day_to,
            user.work_days.time_from,
            user.work_days.time_to,
        )

    result = await connection.fetchrow(
        f'''
            INSERT INTO {USERS_TABLE} (
                login, 
                first_name, 
                last_name,
                work_day_from,
                work_day_to,
                work_time_from,
                work_time_to
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7
            ) RETURNING *;
        ''',
        user.login, user.name.first, user.name.last, *time_kwargs
    )

    return user_row_to_model(result, full=True)


async def get_users_from_event_rows(connection: Connection, event_rows: Iterable[dict]) -> dict[str, User]:
    logins = set()

    for row in event_rows:  # event is row from database
        logins.add(row['author'])
        logins.add(row['user_login'])

    rows = await connection.fetch(
        f'''
            SELECT * FROM {USERS_TABLE} WHERE login = ANY($1::text[]);
        ''',
        logins
    )

    return {
        row['login']: user_row_to_model(row, full=False)
        for row in rows
    }


async def get_one_user(
        connection: Connection, login: str, full=False
) -> Union[UserFull, User]:
    row = await connection.fetchrow(
        f'SELECT * FROM {USERS_TABLE} WHERE login = $1',
        login
    )

    return user_row_to_model(row, full=full)


async def get_many_users(connection: Connection, logins: list[str], full=False) -> list[Union[UserFull, User]]:
    rows = await connection.fetch(
        f'SELECT * FROM {USERS_TABLE} WHERE login = ANY($1::text[])',
        set(logins)
    )

    return [user_row_to_model(row, full=full) for row in rows]


async def get_user_by_session(connection: Connection, session_id: str) -> Optional[User]:
    if session_id is None:
        return

    row = await connection.fetchrow(
        f'''SELECT * FROM {USERS_TABLE} WHERE session_id = $1 LIMIT 1;''',
        session_id
    )

    return user_row_to_model(row, full=False)


async def set_user_session_id(connection: Connection, login: str, session_id: str) -> bool:
    if session_id is None:
        raise ValueError('session_id is empty')

    row = await connection.fetch(
        f'''UPDATE {USERS_TABLE} SET session_id = $1 WHERE login = $2 RETURNING 1;''',
        session_id, login
    )

    return bool(row)
