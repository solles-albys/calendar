from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from lib.api.models.common import EDay, Time


class Name(BaseModel):
    first: str
    last: str


class WorkDays(BaseModel):
    day_from: EDay
    day_to: EDay
    time_from: Time
    time_to: Time


class User(BaseModel):
    login: str
    name: Name


class UserFull(BaseModel):
    login: str
    name: Name
    work_days: Optional[WorkDays] = None


class ReqUserEvents(BaseModel):
    login: str
    time_from: datetime
    time_to: datetime

