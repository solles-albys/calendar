from pydantic import BaseModel
from datetime import timedelta, datetime


class RCalcFreeTime(BaseModel):
    event_duration: timedelta
    start_calc_from: datetime
    user_logins: set[str]


class FreeTime(BaseModel):
    start: datetime = None
    end: datetime = None
