"""
Module realize validators for query params.
"""
import re
import pytz
from dateutil import parser, tz
from datetime import datetime
from typing import List


def isUUID4(uuidStr: str) -> bool:
    """
    Checking uuidStr is uuid4 in format '^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}\Z' or not.

    Args:
        uuidStr: some string
    Returns:
        true if uuidStr is uuid4 else false
    >>> isUUID4("af3fb041-1a55-43e6-9ac2-a361aa432951")
    True
    >>> isUUID4("af3fb041-1a55-43e6-9ac2-a361aa43295")
    False
    >>> isUUID4("af3fb0411a5543e69ac2a361aa432951")
    False
    """
    regex = re.compile('^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}\Z', re.I)
    match = regex.match(uuidStr)
    return True if bool(match) else False


def uuid4Getter(value: str) -> str:
    """
    Get uuid4 value.

    Args:
        value: some string
    Raises:
        ValueError: if value is not uuid4
    Returns:
    value if  it is uuid4
    """
    if isUUID4(value):
        return value
    raise ValueError


def timeFilterGetter(value: str, inLocalTime: bool = True) -> datetime:
    """
    Getting time filter. If time in request not ends with 'Z', but storage_time is UTC, it will be converted to UTC

    Args:
        value: time string in isoformat "YYYY-MM-DDThh:mm:ss.sTZD" (eg 1997-07-16T19:20:30.45+01:00) or
               "YYYY-MM-DDThh:mm:ss.sZ"
        inLocalTime: return ti
    Returns:
        datetime object without timezone
    >>> timeFilterGetter("10-12-2018T12:00:00+03:00")
    datetime.datetime(2018, 10, 12, 12, 0)

    >>> timeFilterGetter("10-12-2018T12:00:00+03:00", False)
    datetime.datetime(2018, 10, 12, 9, 0)

    >>> timeFilterGetter("10-12-2018T12:00:00Z")
    datetime.datetime(2018, 10, 12, 15, 0)

    >>> timeFilterGetter("10-12-2018T12:00:00Z", False)
    datetime.datetime(2018, 10, 12, 12, 0)
    """
    datetimeValue = parser.parse(value.replace(' ', '+'))
    if not value.endswith('Z') and not inLocalTime:
        return datetimeValue.astimezone(pytz.UTC).replace(tzinfo=None)
    elif inLocalTime:
        return datetimeValue.astimezone(tz.tzlocal()).replace(tzinfo=None)
    else:
        return datetimeValue.replace(tzinfo=None)


def listUUIDsGetter(value: str) -> List[str]:
    """
    Validate list of uuid

    Args:
        value:coma separate uuid4
    Returns:
        list of uuid4
    >>> listUUIDsGetter("af3fb041-1a55-43e6-9ac2-a361aa432951,98d92aef-8ba9-4b58-a0d9-fcc915160e9d")
    ['af3fb041-1a55-43e6-9ac2-a361aa432951', '98d92aef-8ba9-4b58-a0d9-fcc915160e9d']
    """
    uids = value.split(",")
    for uid in uids:
        uuid4Getter(uid)
    return uids


def int01Getter(value: str) -> int:
    """
    Validate int.

    Args:
        value: value 0,1
    Raises:
        ValueError if value not in (0, 1)
    Returns:
        int 0 or 1
    """
    value = int(value)
    if value not in (0, 1):
        raise ValueError
    return value


def float01Getter(value: str) -> float:
    """
    Validate float.

    Args:
        value: value 0,1
    Raises:
        ValueError if value not in (0, 1)
    Returns:
        float between 0 and 1
    """
    value = float(value)
    if value not in (0, 1):
        raise ValueError
    return value
