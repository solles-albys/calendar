import argparse
import logging.config

import uvicorn
import uvloop
from fastapi import FastAPI

from lib.api import auth, events, funcs, users
from lib.config import parse_config
from lib.db import Database
from lib.modules.notificator import Notificator  # noqa
from lib.modules.auth import Auth  # noqa
from lib.sql import create_tables
from lib.util.module import get_all_module_classes

uvloop.install()

app = FastAPI(title='Calendar')

app.include_router(events.router)
app.include_router(funcs.router)
app.include_router(users.router)
app.include_router(auth.router)


@app.on_event("shutdown")
async def on_shutdown():
    for module in get_all_module_classes():
        obj = module()
        await obj.on_shutdown()


@app.on_event("startup")
async def on_start():
    config = parse_config('config.yaml')

    logging.config.dictConfig(config['logging'])

    # initialize modules with configs
    for module in get_all_module_classes():
        if module.CONFIG_KEY:
            module(config[module.CONFIG_KEY])
        else:
            module(None)

    async with Database().connect() as connection:
        await create_tables(connection)

    Notificator().start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p', type=int, default=8000)
    parser.add_argument('--host', '-H', type=str, default='::')
    parser.add_argument('--reload', '-r', action='store_true', default=False)

    parser.add_argument('--config', '-c', type=str, help='Path to configuration yaml file')
    args = parser.parse_args()

    # TODO: set uvicorn server log config from file
    uvicorn.run('main:app', host=args.host, port=args.port, reload=True, loop="uvloop")
