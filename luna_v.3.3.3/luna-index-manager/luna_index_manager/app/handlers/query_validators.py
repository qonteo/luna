"""
Module realize validators for query params.
"""
import re
from enum import Enum
from typing import List

from db.models import TaskStatus


class QueueActions(Enum):
    """
    Enum for action with crawler buffer QueueActions
    """
    FORWARD = "forward"     #: forward list to the head of the queue
    CLEAN = "clear"         #: clear queue


def actionValidator(value: str) -> str:
    if value not in [enum.value for enum in QueueActions]:
        raise ValueError
    return value


def listStringsGetter(value: str) -> List[str]:
    """
    Split string by comma

    Args:
        value: string
    Returns:
        list of string

    >>> listStringsGetter("1,ab")

    ["1", "ab"]

    """
    return value.split(",")


def statusGetter(value: str) -> int:
    """
    Validate that

    Args:
        value:  string as int

    Returns:
        converted to int value
    Raises:
        ValueError: if value does not belong to set of values of task status
    """
    status = int(value)
    if status not in (TaskStatus.FAILED, TaskStatus.SUCCESS, TaskStatus.CANCELLED):
        raise ValueError
    return status
