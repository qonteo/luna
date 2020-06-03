from functools import wraps
import time
from tornado import gen


class Timer:
    """
    Timer class.

    Attributes:
        logger (Logger): logger to log timer results
    """
    logger = None

    def __init__(self, logger):
        self.logger = logger

    def timerTor(self, func):
        """
        Decorator for asynchronous function work time estimation.

        :param func: decorated function.
        :return: wrapped function
        """

        @wraps(func)
        @gen.coroutine
        def wrap(*func_args, **func_kwargs):
            if __debug__:
                start = time.time()
                res = yield func(*func_args, **func_kwargs)
                end = time.time()
                self.logger.debug(func.__qualname__ + " time: " + str(round(end - start, 5)))
                return res
            else:
                res = yield func(*func_args, **func_kwargs)
                return res

        return wrap

    def timer(self, func):
        """
        Decorator for synchronous function work time estimation.

        :param func: decorated function.
        :return: wrapped function
        """

        @wraps(func)
        def wrap(*func_args, **func_kwargs):
            if __debug__:
                start = time.time()
                res = func(*func_args, **func_kwargs)
                end = time.time()
                self.logger.debug(func.__qualname__ + " time: " + str(round(end - start, 5)))
                return res
            else:
                res = func(*func_args, **func_kwargs)
                return res

        return wrap
