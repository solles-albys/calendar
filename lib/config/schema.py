from lib.util.module import get_all_module_classes
from lib.db import Database

_SCHEMA = {

}


def initialize_schema():
    for module_class in get_all_module_classes():
        _SCHEMA[module_class.CONFIG_KEY] = module_class.CONFIG_SCHEME
