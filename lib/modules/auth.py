from logging import getLogger
from typing import Optional
from uuid import uuid4

from lib.models.users import User
from lib.sql.user import get_user_by_session, set_user_session_id
from lib.util.module import BaseModule, SingletonModule

logger = getLogger('auth')


class Auth(BaseModule, metaclass=SingletonModule):
    def __init__(
            self,
            config: dict = None,
            loop=None
    ):
        super(Auth, self).__init__(config, loop)

    @staticmethod
    async def authorize(connection, session_id: str) -> Optional[User]:
        return await get_user_by_session(connection, session_id)

    @staticmethod
    async def create_session(connection, login: str) -> str:
        session_id = str(uuid4())
        if await set_user_session_id(connection, login, session_id):
            return session_id
