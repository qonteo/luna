import ujson as json
from enum import Enum

from common.helpers import getNowTimestampMillis


class TaskType(Enum):
    HIT_TOP_N = 'hit_top_n'
    CLUSTERIZATION = 'clusterization'
    LINKER = 'linker'
    CROSS_MATCHER = 'cross_matcher'
    REPORTER = 'reporter'
    UNKNOWN_TYPE = "unknown_type"

    def __eq__(self, other):
        return self.value == other

    def __repr__(self):
        return str(self.value)


class TaskStatus(Enum):
    STARTED = "started"
    IN_PROGRESS = "in progress"
    CANCELED = "cancelled"
    FAILED = "failed"
    SUCCESS = "done"

    def __eq__(self, other):
        return self.value == other

    def __repr__(self):
        return str(self.value)


class Task:
    """
    Task.

    Attributes:
        id (int): the unique task id
        status (TaskStatus): the current task status
        progress (float): the task progress (from 0 to 1)
        task (dict): task parameters
        last_update (timestamp): last task update time in rfc3339
        create_time (timestamp): task create time in rfc3339
        type (taskType): a task type
        result (dict): a task result
    """
    def __init__(self, taskType: TaskType, params):
        """
        :param taskType: task type
        :param params: task parameters
        """
        self.id = None
        self.status = TaskStatus.STARTED.value
        self.progress = 0
        self.task = params
        self.last_update = getNowTimestampMillis()
        self.create_time = getNowTimestampMillis()
        self.type = taskType.value
        self.result = {}

    @property
    def json(self):
        """
        Create json from self.__dict__

        :return: json as string
        """
        taskDict = self.__dict__.copy()
        return json.dumps(taskDict, ensure_ascii = False)

    @staticmethod
    def generateTaskFromDict(task: dict):
        """
        Generate task from dict

        :param task: task dict
        :return: generated task
        """
        newTask = Task(TaskType.UNKNOWN_TYPE, None)
        newTask.__dict__ = task
        return newTask

    def update_last_update(self):
        """
        Update last_update task field

        :return: None
        """
        self.last_update = getNowTimestampMillis()

    def addError(self, result):
        """
        Add error to the task. Error count limit is 1k.

        :param result: Result object with an error
        :return: None
        """
        if "errors" not in self.result:
            self.result["errors"] = {"total": 1}
            self.result["errors"]["errors"] = [{'error_code': result.errorCode, 'detail': result.description}]
        else:
            if self.result["errors"]["total"] < 1000:
                self.result["errors"]["errors"].append({'error_code': result.errorCode, 'detail': result.description})
            self.result["errors"]["total"] += 1

    def success(self, result):
        """
        Finish task with a success result.

        :param result: result to get result from
        :return: None
        """
        self.update_last_update()
        self.progress = 1
        self.result["success"] = result
        self.status = TaskStatus.SUCCESS.value