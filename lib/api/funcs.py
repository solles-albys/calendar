from fastapi import APIRouter

from lib.models.funcs import RCalcFreeTime, FreeTime
from lib.sql.funcs import get_users_busy_time
from lib.db import Database
from datetime import datetime

router = APIRouter(
    prefix='/funcs'
)


class IterUsersTimes:
    def __init__(self, connection, request: RCalcFreeTime, stop_after_iterations=5):
        self.connection = connection
        self.request = request
        self.stop_after_iteration = stop_after_iterations
        self.start_time = request.start_calc_from
        self.values = []

    def __aiter__(self):
        return self

    async def preload(self):
        if self.values:
            raise RuntimeError('Already loaded data')

        self.stop_after_iteration -= 1
        self.values = await get_users_busy_time(self.connection, self.request.user_logins, self.start_time)

    async def __anext__(self) -> tuple[datetime, datetime]:
        if self.values:
            value = self.values.pop(0)
            self.start_time = value[1]
            return value

        self.stop_after_iteration -= 1
        if self.stop_after_iteration:
            raise StopAsyncIteration

        self.values = await get_users_busy_time(self.connection, self.request.user_logins, self.start_time)
        if not self.values:
            raise StopAsyncIteration

        value = self.values.pop(0)
        self.start_time = value[1]
        return value


@router.post('/calc_free_slot')
async def calculate_free_slot(request: RCalcFreeTime):
    async with Database().connect(read_only=True) as connection:
        busy_times = IterUsersTimes(connection, request, stop_after_iterations=5)
        await busy_times.preload()

        try:
            first = await busy_times.__anext__()
        except StopAsyncIteration:
            first = None

        if not first or first[0] - request.start_calc_from >= request.event_duration:
            return FreeTime(
                start=request.start_calc_from,
                end=request.start_calc_from + request.event_duration
            )

        prev_end = first[1]
        async for time_start, time_end in busy_times:
            if prev_end < time_start and time_start - prev_end >= request.event_duration:
                return FreeTime(
                    start=prev_end,
                    end=prev_end + request.event_duration,
                )

            prev_end = max(prev_end, time_end)

    return FreeTime()
