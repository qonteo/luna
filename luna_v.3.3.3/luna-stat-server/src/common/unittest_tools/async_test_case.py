import asyncio
from functools import wraps


def coroutine_function_decorator(func):
    @wraps(func)
    def wrapper(*args, **kw):
        return asyncio.get_event_loop().run_until_complete(func(*args, **kw))

    return wrapper


class AsyncTestCaseMixin(object):
    def __new__(cls, *args, **kwargs):
        inst = super().__new__(cls)
        inst.__init__(*args, *kwargs)
        for name, field in (
            (name, getattr(inst, name))
            for name in dir(inst)
            if name.startswith('test')
        ):
            if asyncio.iscoroutinefunction(field):
                inst.__dict__[name] = coroutine_function_decorator(field)

        return inst
