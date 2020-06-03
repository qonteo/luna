"""
Module realize  getting and checking request id

Attributes:
    TIME_ZONE_DELTA: time zone of machine
"""
import time
import uuid

from typing import Optional

from .regexps import REQUEST_ID_REGEXP

TIME_ZONE_DELTA = time.timezone     #: correction for getting timestamp in utc

LOCAL_TIME = True                   #: generate timestamp in local time


def generateRequestId(localTime: Optional[bool] = None) -> str:
    """
    Generate correct request id.

    Args:
        localTime: timestamp generate in localtime or not
    Returns:
        standard request id string.
    """
    global LOCAL_TIME

    if localTime is None:
        if LOCAL_TIME:
            requestId = "{},{}".format(int(time.time() - TIME_ZONE_DELTA), str(uuid.uuid4()))
        else:
            requestId = "{},{}".format(int(time.time()), str(uuid.uuid4()))

    elif localTime:
        requestId = "{},{}".format(int(time.time() - TIME_ZONE_DELTA), str(uuid.uuid4()))
    else:
        requestId = "{},{}".format(int(time.time()), str(uuid.uuid4()))
    return requestId


def setLocalTime(localTime: bool):
    """
    Update global setting LOCAL_TIME
    Args:
        localTime: timestamp generate in localtime or not
    """
    global LOCAL_TIME
    LOCAL_TIME = localTime


def checkRequestId(requestId: str) -> bool:
    """
    Validate request id str

    Args:
        requestId: str for checking

    Returns:
        True if requestId match with REQUEST_ID_REGEXP otherwise False
    """
    match = REQUEST_ID_REGEXP.match(requestId)
    return match is not None
