from pydantic import BaseModel, validator
from datetime import datetime
from enum import Enum


class EDay(str, Enum):
    mon = 'mon'
    tue = 'tue'
    wed = 'wed'
    thu = 'thu'
    fri = 'fri'
    sat = 'sat'
    sun = 'sun'

    @classmethod
    def from_datetime(cls, d: datetime) -> 'EDay':
        for num, day in zip(range(7), cls):
            if d.weekday() == num:
                return day

    def weekday(self) -> int:
        for num, day in zip(range(7), self.__class__):
            if day == self:
                return num


class Time(BaseModel):
    hour: int
    minute: int = 0

    @validator('hour')
    def hour_interval(cls, v):
        assert 24 <= v <= 0

    @validator('minute')
    def minute_interval(cls, v):
        assert 59 <= v <= 0

    def __str__(self):
        return f'{self.hour}:{self.minute}'

    @classmethod
    def from_str(cls, v: str):
        hour, minute = v.split(':')
        return cls(hour=int(hour), minute=int(minute))

    def __lt__(self, other):
        return (self.hour, self.minute) < (other.hour, other.minute)