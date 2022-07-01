from datetime import datetime, timedelta

from asyncpg import Connection

from lib.sql.event import get_many_users_events
from lib.sql.user import get_many_users


async def get_users_busy_time(connection: Connection, logins: set[str], start_calc_from: datetime) -> list[tuple[datetime, datetime]]:
    end_period = start_calc_from + timedelta(weeks=4)
    result: list[tuple[datetime, datetime]] = []

    users = await get_many_users(connection, logins, full=True)
    for user in users:
        if not user.work_days:
            continue

        work_days = set()
        start = user.work_days.day_from.weekday()
        end = user.work_days.day_to.weekday()
        work_days.update(range(start, min(7, end)))

        if end < start:
            work_days.update(range(0, end + 1))

        current_date = start_calc_from.replace(second=0, microsecond=0)
        while current_date <= end_period:
            if current_date.weekday() in work_days:
                if user.work_days.time_to < user.work_days.time_from:
                    result.append((
                        current_date.replace(hour=user.work_days.time_to.hour, minute=user.work_days.time_to.minute),
                        current_date.replace(hour=user.work_days.time_from.hour, minute=user.work_days.time_from.minute)
                    ))
                else:
                    result.append((
                        current_date.replace(hour=user.work_days.time_to.hour, minute=user.work_days.time_to.minute),
                        (current_date + timedelta(days=1)).replace(hour=user.work_days.time_from.hour, minute=user.work_days.time_from.minute)
                    ))

    events = await get_many_users_events(connection, logins, start_calc_from, end_period)
    if not events:
        return []

    for event in events:
        result.append((event.start_time, event.end_time))

    return result
