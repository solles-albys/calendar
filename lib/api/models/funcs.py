from pydantic import BaseModel
from datetime import timedelta, datetime


class RCalcFreeTime(BaseModel):
    event_duration: timedelta
    start_calc_from: datetime
    user_logins: list[str]
