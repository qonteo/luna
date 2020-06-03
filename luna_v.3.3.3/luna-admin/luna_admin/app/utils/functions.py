"""
Additional functions module
"""
from typing import Optional
from time import time
from uuid import uuid4


def getRequestId(requestId: Optional[str] = None) -> str:
    """
    Returns requestId if exists, else generate it
    Args:
        requestId: luna request id
    Returns:
        requestId
    """
    return str(requestId) if requestId else "{},{}".format(int(time()), str(uuid4()))
