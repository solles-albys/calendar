from .user import create_table_users
from .event import create_table_events
from .participation import create_table_participation


async def create_tables(connection):
    await create_table_users(connection)
    await create_table_events(connection)
    await create_table_participation(connection)


__all__ = ('create_tables',)
