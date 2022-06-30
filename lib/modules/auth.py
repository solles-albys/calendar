from lib.util.module import BaseModule
from lib.db import Database
from lib.sql.user import get_user_by_session, set_user_session_id
from lib.api.models.users import User
from typing import Optional

from logging import getLogger
from uuid import uuid4


logger = getLogger('auth')


class Auth(BaseModule):
    def __init__(
            self,
            config: dict = None,
            loop=None
    ):
        super(Auth, self).__init__(config, loop)

    @staticmethod
    def authorize(session_id: str) -> Optional[User]:
        async with Database().connect(read_only=True) as connection:
            return await get_user_by_session(connection, session_id)

    @staticmethod
    def create_session(login: str) -> str:
        session_id = str(uuid4())
        async with Database().connect() as connection:
            if await set_user_session_id(connection, login, session_id):
                return session_id
