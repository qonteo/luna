"""
Module realize useful function.
"""
import inspect

from datetime import datetime
from dateutil import tz


def isCoroutineFunction(func: callable) -> bool:
    """
    Check function is coroutine or not.
    Args:
        func: some func

    Returns:
        true if  func is coroutine otherwise false
    """
    return (getattr(func, '_is_coroutine', False) or
            inspect.iscoroutinefunction(func)) or getattr(func, '__tornado_coroutine__', False)


def convertTimeToString(inputDateTime: datetime, inUTC: bool = False) -> str:
    """
    Function adds current time zone and isoformat(T) to datetime object if storage_time is local or 'Z' if UTC
    Args:
        inputDateTime: datetime object
        inUTC: return time in UTC format or local
    Returns:
        string, format: "YYYY-MM-DDThh:mm:ss.sTZD" (eg 1997-07-16T19:20:30.45+01:00) or "YYYY-MM-DDThh:mm:ss.sZ"

    >>> convertTimeToString(datetime(2018, 10, 12, 12, 0))
    '2018-10-12T12:00:00+03:00'

    >>> convertTimeToString(datetime(2018, 10, 12, 9, 0), True)
    '2018-10-12T09:00:00Z'
    """
    if inUTC:
        return inputDateTime.isoformat('T') + 'Z'
    else:
        return inputDateTime.replace(tzinfo=tz.tzlocal()).isoformat('T')
