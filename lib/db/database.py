import asyncio
import os
from typing import Optional
from asyncpg import Connection

from lib.db.pool import PoolManager
from lib.util.module import BaseModule, SingletonModule


class Database(BaseModule, metaclass=SingletonModule):
    CONFIG_KEY = 'database'
    CONFIG_SCHEME = {
        'type': 'dict',
        'schema': {
            'hosts': {'type': 'list', 'schema': {'type': 'string'}, 'default': []},
            'port': {'type': 'integer', 'default': 6432},
            'dbname': {'type': 'string', 'default': 'calendar_db'},
            'user': {'type': 'string', 'default': 'calendar_admin'},
            'password': {'type': 'string', 'default': os.environ.get('DB_PASSWORD')},
            'min_size': {'type': 'integer', 'default': 1},
            'max_size': {'type': 'integer', 'default': 10},
            'timeout': {'type': 'integer', 'default': 30},
            'master_as_replica_weight': {'type': 'float', 'default': 0.5},
        }
    }

    def __init__(
            self,
            config: dict = None,
            loop: asyncio.AbstractEventLoop = None
    ):
        super().__init__(config)

        self.hosts: list[str] = config['hosts']
        self.port: int = self.config['port']
        self.dbname: str = self.config['dbname']
        self.user: str = self.config['user']
        self.password: str = self.config['password']
        self.min_size: int = self.config['min_size']
        self.max_size: int = self.config['max_size']
        self.timeout: int = self.config['timeout']
        self.master_as_replica_weight: float = self.config['master_as_replica_weight']

        self.pool: Optional[PoolManager] = PoolManager(
            self.dsn,
            pool_factory_kwargs={'min_size': self.min_size, 'max_size': self.max_size},
            fallback_master=True,
            master_as_replica_weight=self.master_as_replica_weight,
            acquire_timeout=self.timeout,
            loop=loop,
        )

    @property
    def dsn(self):
        return f'postgresql://{self.user}:{self.password}@{",".join("%s:%s" % (host, self.port) for host in self.hosts)}/{self.dbname}'

    def connect(self, read_only=False) -> Connection:
        return self.pool.acquire(read_only=read_only, timeout=self.timeout)

    async def close(self):
        await self.pool.close()

    async def on_shutdown(self):
        await self.close()
