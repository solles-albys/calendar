from fastapi import APIRouter, HTTPException
from src.api.models import EventCreateRequest, Event
from src.db import Database
from src.sql import event_sql

router = APIRouter(
    prefix='/event'
)


@router.post('/')
async def create_event(event_create_request: EventCreateRequest) -> Event:
    async with Database().connect() as connection:
        event = await event_sql.insert(connection, event_create_request)

    return event


@router.post('/{event_id}/accept')
async def accept_event_by_user(event_id: int, user_login: str):
    pass


@router.get('/{event_id}')
async def get_event(event_id: int):
    async with Database().connect(read_only=True) as connection:
        result = await event_sql.get_one(connection, event_id)

    if result is None:
        return HTTPException(status_code=404, detail=f'Event {event_id} not found')

    return result




