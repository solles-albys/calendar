import pytest
from fastapi import HTTPException
from lib.api.methods.users import create_user
from lib.api.models.users import UserFull, Name
from lib.sql.const import USERS_TABLE
from tests.full_wait import full_wait_pending


@pytest.mark.asyncio
@full_wait_pending
async def test_create_user(db):
    result = await create_user(UserFull(login='test', name=Name(first='vova', last='last')))
    assert result is None

    result = await create_user(UserFull(login='test', name=Name(first='vova', last='last')))
    assert isinstance(result, HTTPException)

    result = await create_user(UserFull(login='', name=Name(first='vova', last='last')))
    assert isinstance(result, HTTPException)

    async with db.connect() as conn:
        response = await conn.fetch(f'SELECT * FROM {USERS_TABLE};')

    assert len(response) == 1
    assert response[0]['login'] == 'test'

