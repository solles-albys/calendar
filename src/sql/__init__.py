from src.sql import (
    event as event_sql,
    user as user_sql,
    participation as participation_sql
)


async def create_tables(connection):
    await user_sql.create_table(connection)
    await event_sql.create_table(connection)
    await participation_sql.create_table(connection)


__all__ = ('event_sql', 'user_sql', 'participation_sql', 'create_tables')
