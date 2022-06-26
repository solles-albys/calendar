from src.config.schema import _SCHEMA, initialize_schema
import yaml
import cerberus
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
    # FIXME:
    if not _validator.validate(data):
        raise ConfigError(_validator.errors)
    data = _validator.normalized(data)
    return data

