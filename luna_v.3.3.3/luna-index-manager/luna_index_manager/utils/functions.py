"""
Module realize useful function.
"""
from datetime import datetime
from dateutil import parser


def convertToDateTime(dateTimeString: str) -> datetime:
    """
    Convert datetime from string to datetime object, considering timezone
    Args:
        dateTimeString: str with datetime
    Returns:
        datetime with timezone
    """
    if not dateTimeString.endswith('Z'):
        return parser.parse(dateTimeString).replace(tzinfo=None)
    else:
        return parser.parse(dateTimeString).astimezone().replace(tzinfo=None)