from fastapi import APIRouter, HTTPException
from lib.api.models.events import RCreateEvent, Event, EDecision
from lib.db import Database
from lib.sql.event import insert_event, get_one_event
from lib.sql.participation import accept_participation
from asyncpg import exceptions as exc

router = APIRouter(
    prefix='/event'
)


@router.post('/')
async def create_event(event_create_request: RCreateEvent) -> Event:
    async with Database().connect() as connection:
        try:
            event = await insert_event(connection, event_create_request)
        except exc.UniqueViolationError:
            return HTTPException(status_code=400, detail='Event already exists')

    return event


@router.post('/{event_id}/accept')
async def accept_event_by_user(event_id: int, user_login: str, decision: EDecision):
    async with Database().connect() as connection:
        await accept_participation(connection, event_id, user_login, decision)


@router.get('/{event_id}')
async def get_event(event_id: int):
    async with Database().connect(read_only=True) as connection:
        result = await get_one_event(connection, event_id)

    if result is None:
        return HTTPException(status_code=404, detail=f'Event {event_id} not found')

    return result




