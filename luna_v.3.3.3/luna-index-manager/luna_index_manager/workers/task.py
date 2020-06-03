"""
Module realize IndexTask, class for  storage current state of task and interface for update state of task in db.
"""
from datetime import datetime
from enum import Enum

from logbook import Logger

from db.context import DBContext
from db.models import TaskStatus


class IndexStep(Enum):
    """
    Enum for steps of indexing.
    """
    initialize = "initialize"  #: first step, initialize task
    createIndex = "create index"  #: second step, create index in indexer
    uploadIndex = "upload index"  #: third step, upload index to all machine with matchers
    reloadIndex = "reload index"  #: fourthly step, reload indexes on matchers


class IndexTask:
    """
    Luna-face list index task
    Attributes:
        listId: list id in luna-faces
        logger: task logger
        id (int): task id
        dbContext (DBContext): db context
        lastUpdateTime (datetime): last update time
        startTime (datetime): start task time
        step (str): step of indexing
        generation (str): generation from indexer
        status (bool): status of the task, true - index success created otherwise false.
        taskRequestId (str): request id to external services
    """

    def __init__(self, listId: str, logger: Logger, taskRequestId: str):
        self.listId = listId
        self.step = IndexStep.initialize.value
        self.lastUpdateTime = datetime.now()
        self.startTime = datetime.now()
        self.status = None
        self.logger = logger
        self.dbContext = DBContext(logger)
        self.id = self.dbContext.createNewTask(listId)
        self.generation = None
        self.taskRequestId = taskRequestId

    def startIndex(self, generation) -> None:
        """
        Update state of task.

        Index is built now in the indexer. Update the step (IndexStep.createIndex), generation and lastUpdateTime.
        Update task in db.

        Args:
            generation: generation of new index.
        """
        self.step = IndexStep.createIndex.value
        self.generation = generation
        self.lastUpdateTime = datetime.now()
        self.dbContext.updateTaskData(self.id, start_index_time=datetime.now(), generation=generation)

    def finishStep(self, endStepTimeParam) -> None:
        """
        Finish a step of creating index.

        Args:
            endStepTimeParam: kwargs param for updateTaskData corresponding end time of step.
        """
        self.lastUpdateTime = datetime.now()
        self.dbContext.updateTaskData(self.id, **{endStepTimeParam: self.lastUpdateTime})

    def finishIndex(self) -> None:
        """
        Finish build index step, update end_index_time of task in db.
        """
        self.finishStep("end_index_time")

    def startUploadIndex(self) -> None:
        """
        Begin step of upload index.
        """

        self.step = IndexStep.uploadIndex.value
        self.lastUpdateTime = datetime.now()
        self.dbContext.updateTaskData(self.id, start_upload_index_time=datetime.now())

    def finishUploadIndex(self) -> None:
        """
        Finish upload index step, update end_index_time of task in db.
        """
        self.finishStep("end_upload_index_time")

    def startReloadIndex(self) -> None:
        """
        Begin step of index reload.
        """
        self.step = IndexStep.reloadIndex.value
        self.lastUpdateTime = datetime.now()
        self.dbContext.updateTaskData(self.id, start_reload_index_time=datetime.now())

    def finishReloadIndex(self) -> None:
        """
        Finish of reload index step.
        """
        self.finishStep("end_reload_index_time")

    def success(self) -> None:
        """
        Mark task as ok.

        Set status in True and status in db to TaskStatus.success.

        """
        self.status = True
        self.lastUpdateTime = datetime.now()
        self.dbContext.updateTaskData(self.id, end_time=datetime.now(), status=TaskStatus.SUCCESS.value)

    def fail(self, reason) -> None:
        """
        Mark task as failed.

        Put error to db  and set status in False and status in db to TaskStatus.failed.

        Args:
            reason: description of error.
        """
        self.status = False
        self.dbContext.putError(taskId=self.id, msg=reason)
        self.dbContext.updateTaskData(self.id, end_time=datetime.now(), status=TaskStatus.FAILED.value)

    def updateTime(self) -> None:
        """
        Update last update time of task
        """
        self.dbContext.updateTaskData(self.id)
