"""Timers

Timer decorators

Attributes:
    logger (Logger): logger for function without own logger.
"""
import time
from functools import wraps
from typing import Callable

from tornado import gen

from app.utils.functions import isCoroutineFunction
from app.utils.log import Logger

logger = Logger()


def printLogger(self: object, func: callable, duration: float) -> None:
    """
    Print timing to log

    Args:
        self: class instance with logger
        func: measured function
        duration: calling duration of function in secs
    """
    if hasattr(self, "logger"):
        self.logger.debug("{} time: {}".format(func.__qualname__, round(duration, 5)))
    else:
        logger.debug("{} time: {}".format(func.__qualname__, round(duration, 5)))


def timer(func: callable) -> Callable:
    """
    Decorator for function work time estimation.

    Args:
        func: decorating function
    Returns:
        decorated function.
    """
    if isCoroutineFunction(func):
        @gen.coroutine
        @wraps(func)
        def wrap(*func_args, **func_kwargs):
            start = time.time()
            res = yield func(*func_args, **func_kwargs)
            end = time.time()
            printLogger(func_args[0], func, end - start)
            return res
    else:
        @wraps(func)
        def wrap(*func_args, **func_kwargs):
            start = time.time()
            res = func(*func_args, **func_kwargs)
            end = time.time()
            printLogger(func_args[0], func, end - start)
            return res

    return wrap