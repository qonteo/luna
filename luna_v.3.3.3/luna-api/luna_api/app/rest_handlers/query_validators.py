from typing import List
from crutches_on_wheels.handlers.query_getters import *


def actionGetter(value: str) -> str:
    """
    Get action.

    Args:
        value: some string
    Returns:
        value if  it in ("attach", "detach")
    Raises:
        ValueError: if value not in ("attach", "detach")
    """
    if value in ("attach", "detach"):
        return value
    raise ValueError
