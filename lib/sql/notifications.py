from datetime import datetime, timedelta
from typing import Optional, NamedTuple

from lib.api.models.events import Notification, Repetition, Event, ERepeatType, EDecision
from lib.api.models.common import EDay

from asyncpg import Connection
from lib.util.repetitions import set_start_date_due_to_interval
from lib.sql.const import NOTIFICATION_TABLE, EVENTS_TABLE, USERS_TABLE


async def create_table_notifications(connection: Connection):
    await connection.execute(
        f'''
            CREATE TABLE IF NOT EXISTS {NOTIFICATION_TABLE} (
                id                  serial CONSTRAINT {NOTIFICATION_TABLE}_pk primary key,
                offset_notify       varchar(50),
                next_notify_at      timestamp,
                last_notify_at      timestamp,
                channel             varchar(25),
                event_id            integer NOT NULL CONSTRAINT notification_event__fk references {EVENTS_TABLE}
                                        on update cascade  on delete cascade,
                
                recipient           varchar(255) NOT NULL CONSTRAINT notification_user__fk references {USERS_TABLE}
                                        on update cascade on delete cascade 
            );
        '''
    )

    await connection.execute(
        f'''CREATE INDEX IF NOT EXISTS notification_at__indx on {NOTIFICATION_TABLE} (next_notify_at);'''
    )


def count_offset(offset: str) -> timedelta:
    num = int(offset[:-1])

    if offset[-1] == 'm':
        return timedelta(minutes=num)
    elif offset[-1] == 'h':
        return timedelta(hours=num)
    elif offset[-2] == 'd':
        return timedelta(days=num)


async def insert_notifications(connection: Connection, event: Event):
    if event.start_time < datetime.now() and event.repetition is None:
        return

    logins = {event.author.login, *(p.user.login for p in event.participants if p.decision != EDecision.no)}

    start_time = event.start_time
    end_find_start_notify = timedelta(weeks=200)
    if event.repetition.type == ERepeatType.yearly:
        end_find_start_notify = timedelta(weeks=70 * event.repetition.each)

    params = []
    for notification in event.notifications:
        offset = count_offset(notification.offset)

        event_start = event.start_time
        if start_time - offset < datetime.now() + timedelta(minutes=5):
            event_start = set_start_date_due_to_interval(
                repetition=event.repetition,
                event_start_date=event.start_time,
                repeat_start_date=datetime.now() + offset + timedelta(minutes=5),
                repeat_end_date=end_find_start_notify,
            )

        params.extend(
            (notification.offset, notification.channel.value, event_start - offset, event.id, login)
            for login in logins
        )

    await connection.executemany(
        f'''
            INSERT INTO {NOTIFICATION_TABLE} (
                offset_notify,
                next_notify_at,
                channel,
                event_id,
                recipient
            ) VALUES ($1, $2, $3, $4, $5);
        ''',
        params
    )


class NotificationRecord(NamedTuple):
    id: int
    offset_notify: str
    next_notify_at: datetime
    channel: str
    event_id: int
    recipient: str
    last_notify_at: Optional[datetime] = None
    repetition: Optional[Repetition] = None


async def get_pending_notifications(connection: Connection) -> list[NotificationRecord]:
    rows = await connection.fetch(
        f'''
            SELECT n.*, e.repeat_due_date, e.repeat_each, e.repeat_monthly_last_week, e.repeat_type 
                FROM {NOTIFICATION_TABLE} n
            RIGHT JOIN {EVENTS_TABLE} e on e.id = n.event_id
            WHERE n.next_notify_at IS NOT NULL and n.next_notify_at <= $1;
        ''',
        datetime.now() + timedelta(minutes=1)
    )

    result = []
    for row in rows:
        notification = NotificationRecord(
            id=row['id'],
            offset_notify=row['offset_notify'],
            next_notify_at=row['next_notify_at'],
            channel=row['channel'],
            event_id=row['event_id'],
            recipient=row['recipient'],
        )

        if row['repeat_type'] is not None:
            weekly_days = []
            for v in row['repeat_weekly_days'].split(','):
                if v:
                    weekly_days.append(EDay(v))

            notification.repetition = Repetition(
                type=ERepeatType(row['repeat_type']),
                weekly_days=weekly_days,
                monthly_last_week=row['repeat_monthly_last_week'],
                due_date=row['repeat_due_date'],
                each=row['repeat_each'],
            )

        result.append(notification)

    return result
