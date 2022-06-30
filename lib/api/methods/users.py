import os
from datetime import datetime

import asyncpg.exceptions as exc
from fastapi import APIRouter, HTTPException

from lib.api.models.users import UserFull
from lib.db import Database
from lib.sql.user import insert_user, get_one_user
from lib.sql.event import get_user_events as sql_get_user_events

from logging import getLogger

logger = getLogger('api.users')

router = APIRouter(
    prefix='/users'
)


USER_EXISTS = HTTPException(status_code=400, detail='User already exists')


@router.post('/', status_code=201)
async def create_user(user: UserFull):
    if not user.login:
        return HTTPException(status_code=400, detail='User login should not be empty')

    try:
        async with Database().connect() as connection:
            await insert_user(connection, user)
    except exc.UniqueViolationError:
        return HTTPException(status_code=400, detail='User already exists')
    except Exception as e:
        logger.exception('failed to create user')
        return HTTPException(status_code=500)


@router.get('/{login}/events')
async def get_user_events(login: str, time_from: datetime, time_to: datetime):
    async with Database().connect(read_only=True) as connection:
        try:
            await get_one_user(connection, login, full=False)
        except exc.UniqueViolationError:
            return HTTPException(status_code=400, detail='User already exists')
        except Exception as e:
            logger.exception('failed to load user')
            return HTTPException(status_code=500)

        events = await sql_get_user_events(connection, login, time_from, time_to)

    return events
