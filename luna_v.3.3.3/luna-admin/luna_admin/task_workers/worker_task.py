"""
Worker task.
"""


class Task:
    """
    Worker task.

    Attributes:
        target (Union[list, str]): account id or list descriptors
        id (int): task id
        subtask (int): subtask number
        requestId (str): luna request id
    """
    def __init__(self, json: dict, requestId: str) -> None:
        self.target = json["target"]
        self.id = json["task_id"]
        self.subtask = json["subtask"]
        self.taskRequestId = requestId
