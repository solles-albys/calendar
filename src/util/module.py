import abc
import asyncio
import collections
import threading


class SingletonModule(abc.ABCMeta):
    _instances = {}
    _locks = collections.defaultdict(threading.Lock)

    CONFIG_SCHEME: dict
    CONFIG_KEY = None

    def _get_instance_id(cls, args, kwargs):
        return cls

    def __call__(cls, *args, **kwargs):
        with cls._locks[cls]:
            instance_id = cls._get_instance_id(args, kwargs)

            if instance_id not in cls._instances:
                if cls.CONFIG_SCHEME:
                    assert cls.CONFIG_KEY

                cls._instances[instance_id] = super(SingletonModule, cls).__call__(*args, **kwargs)

            return cls._instances[instance_id]


class BaseModule(metaclass=SingletonModule):
    CONFIG_SCHEME: dict
    CONFIG_KEY = None

    def __init__(self, config: dict = None, loop: asyncio.AbstractEventLoop = None):
        super().__init__()

        if self.CONFIG_SCHEME:
            assert self.CONFIG_KEY

        if config is None:
            config = {}

        if loop is None:
            loop = asyncio.get_event_loop()

        self.config = config
        self.loop = loop

    async def on_shutdown(self):
        pass


def get_all_module_classes():
    return BaseModule.__subclasses__()
