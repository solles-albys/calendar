import functools
import asyncio
from typing import Callable


def full_wait_pending(func: Callable):

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        before = set(asyncio.all_tasks())
        result = await func(*args, **kwargs)
        after = set(asyncio.all_tasks())

        for t in after - before:
            if '_check_pool_task' in str(t):
                continue

            try:
                await asyncio.wait_for(t, timeout=None)
            except Exception as e:
                t.cancel()
                continue

        return result

    return wrapper