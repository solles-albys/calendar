from src.api.models import User
from asyncpg import Connection
from src.sql.const import USERS_TABLE


async def create_table(connection: Connection):
    await connection.execute(
        f'''CREATE TABLE IF NOT EXISTS {USERS_TABLE} (
            login varchar(255) CONSTRAINT {USERS_TABLE}_pk primary key
        );'''
    )


async def insert(connection: Connection, user: User) -> User:
    await connection.execute(
        f'INSERT INTO {USERS_TABLE} (login) VALUES ($1);',
        user.login
    )



