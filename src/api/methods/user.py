from fastapi import APIRouter
from src.api import models
from src.sql import user as user_sql

from src.db import Database

router = APIRouter(
    prefix='/user'
)


@router.post('/')
async def create_user(user: models.User):
    db = Database()

    async with db.connect() as connection:
        await user_sql.insert(connection, user)


@router.get('/{login}/events')
async def get_user_events(login: str):
    pass


