import os

import pytest

from lib.util.module import SingletonModule
from lib.db import Database
from lib.sql import create_tables


@pytest.fixture(scope='function')
async def db():
    config = {
        'hosts': os.environ['POSTGRES_RECIPE_HOST'],
        'port': os.environ['POSTGRES_RECIPE_PORT'],
        'dbname': os.environ['POSTGRES_RECIPE_DBNAME'],
        'user': os.environ['POSTGRES_RECIPE_USER'],
        'password': None,
        'min_size': 1,
        'max_size': int(os.environ['POSTGRES_RECIPE_MAX_CONNECTIONS']),
        'timeout': 5,
        'master_as_replica_weight': 0.5,
    }

    # Drop isntances every time to avoid several connections
    SingletonModule._instances.clear()

    database = Database(
        config
    )

    async with database.connect() as connection:
        await connection.execute('CREATE SCHEMA IF NOT EXISTS public;')
        await create_tables(connection)

    try:
        yield database
    finally:
        async with database.connect() as connection:
            await connection.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')
