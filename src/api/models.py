from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime


class User(BaseModel):
    login: str


class EAcceptType(str, Enum):
    accepted = 'accepted'
    optionally = 'optionally'
    declined = 'declined'


class Participant(BaseModel):
    user: User
    accept: EAcceptType = EAcceptType.optionally


class ERepeat(str, Enum):
    daily = 'daily'  # every day
    weakly = 'weakly'  # every weak
    monthly_from_start = 'monthly_from_start'  # every month on exact week from start (f.e. every monday on 4th week)
    monthly_from_end = 'monthly_from_end'  # every month on exact week from end (f.e. last monday)
    yearly = 'yearly'  # every year
    workday = 'workday'  # every workday
    # custom = 'custom'


class EventCreateRequest(BaseModel):
    author: str  # user login
    start_time: datetime
    end_time: datetime
    name: str = 'Новая встреча'
    description: str = ''
    repeat_type: Optional[ERepeat] = None
    participants: list[Participant] = []


class Event(BaseModel):
    id: int
    author: User
    start_time: datetime
    end_time: datetime
    name: str = 'Новая встреча'
    description: str = ''
    repeat_type: Optional[ERepeat] = None
    participants: list[Participant] = []


