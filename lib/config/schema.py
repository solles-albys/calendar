from lib.util.module import get_all_module_classes

_SCHEMA = {
    'logging': {
        'type': 'dict',
        'default': {},
        'schema': {
            'loggers': {
                'type': 'list',
                'schema': {'type': 'string'},
                'default': []
            },
            'filename': {'type': 'string', 'default': ''},
            'root': {
                'type': 'string',
                'default': '/logs'
            },
            'backupCount': {
                'type': 'integer',
                'default': 5
            },
            'maxBytes': {'type': 'integer', 'default': 104857600}  # 100mb
        }
    }
}


def initialize_schema():
    for module_class in get_all_module_classes():
        _SCHEMA[module_class.CONFIG_KEY] = module_class.CONFIG_SCHEME
