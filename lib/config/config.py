from lib.config.schema import _SCHEMA, initialize_schema
import yaml
import cerberus
from copy import deepcopy
import os
from functools import lru_cache

_validator = cerberus.Validator(_SCHEMA)


class ConfigError(Exception):
    pass


@lru_cache()
def parse_config(filename: str) -> dict:
    initialize_schema()

    content = _read_file(filename)
    config = _parse_config(content)
    return config


def _read_file(filename):
    if not filename:
        raise ConfigError(f'invalid config file: {filename}')
    with open(filename, encoding='utf-8') as f:
        return f.read()


def _parse_config(content: str) -> dict:
    data = yaml.load(content, Loader=yaml.FullLoader)
    # if not _validator.validate(data):
    #     raise ConfigError(_validator.errors)
    data = _validator.normalized(data)

    data['logging'] = _standartize_logging(data.get('logging'))

    return data


def _standartize_logging(section: dict):
    development = bool(os.environ.get('DEV_MODE', 0))

    section = section or {}
    result = deepcopy(_default_logging)
    filename = section.get('filename')

    if not filename and development:
        del result['handlers']['file']
        return result

    if not filename:
        root = section['root']
        service_name = os.getenv('SERVICE_ID', "calendar")
        filename = f'{root}/{service_name}.log'

    file_handler = result['handlers']['file']
    file_handler['filename'] = filename
    file_handler['maxBytes'] = section.get('maxBytes')
    file_handler['backupCount'] = section.get('backupCount')

    handlers = ['file']
    if section.get('write_to_stdout'):
        handlers += ['stdout']

    for logger in result['loggers'].values():
        logger['handlers'] = handlers

    return result


_default_logging = {
    'version': 1,
    'formatters': {
        'default': {
            '()': 'lib.logger.formatter.SplittedFormatter',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': None,  # Необходимо установить.
            'encoding': 'utf-8',
            'formatter': 'default',
        },
        'stdout': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default',
        },
    },
    'loggers': {
        'notificator': {
            'handlers': ['stdout'],
            'level': 'DEBUG',
        },
        'asyncpg.pool': {
            'handlers': ['stdout'],
            'level': 'DEBUG',
        }
    },
}