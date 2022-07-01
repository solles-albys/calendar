from fastapi import APIRouter, HTTPException
from lib.modules.auth import Auth
from lib.db import Database

router = APIRouter(
    prefix='/auth'
)


@router.post('/')
async def create_session(login: str):
    async with Database().connect() as connection:
        return await Auth().create_session(connection, login)
