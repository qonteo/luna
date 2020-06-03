import re
from typing import List
from app.admin_db.db_context import TaskType

UUIDre = re.compile('^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}\Z', re.I)


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

    match = UUIDre.match(uuidStr)
    return True if bool(match) else False


def uuid4Getter(value: str) -> str:
    """
    uuid4 getter.

    Args:
        value: some string
    Returns:
        value
    Raises:
        ValueError: if value is not uuid4 will raise exception
    """
    if isUUID4(value):
        return value
    raise ValueError


def listUUIDsGetter(value: str) -> List[str]:
    """
    List uuid4 getter.

    Args:
        value: comma separate uuid4
    Returns:
        list uuid4
    Raises:
        ValueError: if value is not list of uuid4 will raise exception

    >>> listUUIDsGetter("af3fb041-1a55-43e6-9ac2-a361aa43295,af3fb041-1a55-43e6-9ac2-a361aa43295")
    ["af3fb041-1a55-43e6-9ac2-a361aa43295","af3fb041-1a55-43e6-9ac2-a361aa43295"]
    """
    uids = value.split(",")
    for uid in uids:
        uuid4Getter(uid)
    return uids


def getterGCNonLinkedFacesTaskType(value: str) -> TaskType:
    """
    Task type getter.

    Args:
        value:

    Returns:
        TaskType.descriptorsGC
    Raises:
        ValueError: if value not in ["descriptors"] will raise exception
    """
    if value not in ["descriptors"]:
        raise ValueError
    else:
        return TaskType.descriptorsGC


def getterTaskType(value: str) -> TaskType:
    if value not in ("descriptors", "reextract"):
        raise ValueError
    elif value == "descriptors":
        return TaskType.descriptorsGC
    else:
        return TaskType.reExtractGC


def getterTarget(value: str) -> str:
    """
    Task target getter.

    Args:
        value: query parameter

    Returns:
        value
    Raises:
        ValueError: if value not in ["all", "account"] will raise exception
    """
    if value not in ["all", "account"]:
        raise ValueError
    return value


def int01Getter(value) -> int:
    """
    0 or 1 getter

    Args:
        value "0","1"
    Returns:
        0 or 1
    Raises:
        ValueError: if value not in (0, 1) will raise exception

    """
    value = int(value)
    if value not in (0, 1):
        raise ValueError
    return bool(value)
