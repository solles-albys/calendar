import asyncio
from asyncpg import Connection
from typing import Optional
from datetime import datetime, timedelta

from lib.util.module import BaseModule, SingletonModule
from lib.db import Database
from lib.models.events import ERepeatType
from lib.sql.notifications import get_pending_notifications, NotificationRecord, count_offset, update_notifications
from lib.util.repetitions import set_start_date_due_to_interval

from logging import getLogger


logger = getLogger('notificator')


class Notificator(BaseModule, metaclass=SingletonModule):
    def __init__(
            self,
            config: dict = None,
            loop: asyncio.AbstractEventLoop = None
    ):
        super().__init__(config, loop)

        self.task: asyncio.Task = None

    async def on_shutdown(self):
        self.task.cancel('shutdown')

    def start(self):
        self.task = asyncio.create_task(self.notification_loop())

    async def notification_loop(self):
        logger.info(f'started loop {self.__class__.__name__}.{self.notification_loop.__name__}')
        while True:
            try:
                async with Database().connect() as connection:
                    await self.run_once(connection)

            except (asyncio.CancelledError, KeyboardInterrupt, SystemExit):
                return

            except Exception as e:
                logger.exception('notificator crashed')

            await asyncio.sleep(30.0)

    async def run_once(self, connection: Connection):
        notifications = await get_pending_notifications(connection)
        if not notifications:
            return

        to_update_times: list[tuple[int, Optional[datetime], Optional[datetime]]] = []

        for notification in notifications:
            await self.send_notification(notification)

            last_send_time = datetime.now()
            next_notification_time = None

            if notification.repetition is not None:
                next_notification_time = self.find_next_notification_time(notification)

            to_update_times.append(
                (notification.id, next_notification_time, last_send_time)
            )

        await update_notifications(connection, to_update_times)

    @staticmethod
    def find_next_notification_time(notification: NotificationRecord) -> Optional[datetime]:
        start_date = notification.next_notify_at

        offset = count_offset(notification.offset_notify)

        end_find_start_notify = timedelta(weeks=200)
        if notification.repetition.type == ERepeatType.yearly:
            end_find_start_notify = timedelta(weeks=70 * notification.repetition.each)

        next_start_date = set_start_date_due_to_interval(
            repetition=notification.repetition,
            event_start_date=start_date,
            repeat_start_date=datetime.now() + offset + timedelta(minutes=5),
            repeat_end_date=datetime.now() + end_find_start_notify
        )

        return next_start_date

    @staticmethod
    async def send_notification(notification: NotificationRecord):
        logger.debug(
            f'notification: to {notification.recipient} '
            f'via {notification.channel} about event {notification.event_id}'
        )
