from datetime import datetime, timedelta

from asyncpg import Connection

from lib.sql.event import get_many_users_events


async def get_users_busy_time(connection: Connection, logins: set[str], start_calc_from: datetime) -> list[tuple[datetime, datetime]]:
    end_period = start_calc_from + timedelta(weeks=4)

    events = await get_many_users_events(connection, logins, start_calc_from, end_period)
    if not events:
        return []

    result: list[tuple[datetime, datetime]] = []

    for event in events:
        result.append((event.start_time, event.end_time))

    return result
