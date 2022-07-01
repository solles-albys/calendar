import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, validator

from lib.models.common import EDay
from lib.models.users import User


class EDecision(str, Enum):
    yes = 'yes'
    maybe = 'maybe'
    no = 'no'
    undecided = 'undecided'


class Participant(BaseModel):
    user: User
    decision: EDecision = EDecision.undecided


class ERepeatType(str, Enum):
    daily = 'daily'  # every day
    weakly = 'weakly'  # every weak
    monthly_number = 'monthly_number'  # every month
    monthly_day_weekno = 'monthly_day_weekno'  # every week of month
    yearly = 'yearly'  # every year
    workday = 'workday'  # every workday


class Repetition(BaseModel):
    type: ERepeatType
    weekly_days: list[EDay] = []
    monthly_last_week: bool = False  # last week of month
    due_date: Optional[datetime] = None
    each: int = 1


class EChannel(str, Enum):
    sms = 'sms'
    email = 'email'
    telegram = 'telegram'
    slack = 'slack'


NOTIFICATION_OFFSET_RE = re.compile(r'\d+[mhd]')


class Notification(BaseModel):
    channel: EChannel
    offset: str

    @validator('offset')
    def validate_offset_expression(cls, value):
        match = NOTIFICATION_OFFSET_RE.fullmatch(value)

        if not match:
            raise ValueError('offset should have format [0-9]+[mhd]')

        num = int(value[:-1])
        if value[-1] == 'm':
            result = timedelta(minutes=num)
        elif value[-1] == 'h':
            result = timedelta(hours=num)
        elif value[-1] == 'd':
            result = timedelta(days=num)
        else:
            raise ValueError(f'unknown offset type: {value[-1]}')

        if result > timedelta(days=50):
            raise ValueError('offset should be less then 50 days')

        return value


class Event(BaseModel):
    id: int
    author: User
    start_time: datetime
    end_time: datetime
    name: str = 'Новая встреча'
    description: str = ''
    notifications: list[Notification] = []
    participants: list[Participant] = []
    repetition: Optional[Repetition] = None


class RCreateEvent(BaseModel):
    author_login: str
    start_time: datetime
    end_time: datetime
    name: str = 'Новая встреча'
    description: str = ''
    repetition: Optional[Repetition] = None
    notifications: list[Notification] = []
    participants: list[Participant] = []
