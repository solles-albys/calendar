from typing import Optional

from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from lib.api.models.users import User
from lib.api.models.common import EDay


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


class Notification(BaseModel):
    channel: EChannel
    offset: str


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
