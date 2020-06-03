"""
Logger realize worker for removing non linked faces of account.
"""
import datetime
from time import time
from typing import List, Generator, Optional
from logbook import Logger
from luna3.common.exceptions import LunaApiException
from tornado import gen
from app.admin_db.db_context import DBContext
from common.luna_core_error import generateLunaCoreRequestError
from crutches_on_wheels.utils.timer import timer
from app.stats_sender import sendGCListsStats, StatsType
from crutches_on_wheels.errors.errors import ErrorInfo
from crutches_on_wheels.errors.exception import VLException
from configs.config import SEND_TO_LUNA_IMAGE_STORE, LUNA_IMAGE_STORE_PORTRAITS_BUCKET, \
    LUNA_IMAGE_STORE_WARPED_IMAGES_BUCKET
from app.utils.functions import getRequestId
from common.api_clients import STORE_WARPS_CLIENT, STORE_PORTRAITS_CLIENT, CORE_CLIENT, FACES_CLIENT
from task_workers.worker_task import Task


@timer
@gen.coroutine
def removeDescriptorsFromLuna(descriptors: List[str], logger: Logger, requestId: Optional[str] = None) \
        -> Generator[None, None, None]:
    """
    Remove descriptors from luna core
    Args:
        descriptors: list of descriptors for removing
        requestId: luna request id
        logger: logger
    Raises:
        VLException: if status code of response does not  equal to 204
    """
    response = yield CORE_CLIENT.deleteDescriptor(descriptors, asyncRequest=True, lunaRequestId=requestId)

    if response.statusCode != 204:
        error = generateLunaCoreRequestError(response, logger)
        raise VLException(error)


@timer
@gen.coroutine
def removePortraitsAndWarpsFromLunaImageStore(imageIds: List[str]) -> Generator[None, None, None]:
    """
    Remove portraits and warps from luna-image-store

    Args:
        imageIds: list ids for removing
    """
    countRequests = int((len(imageIds) + 999) / 1000)
    sizeCoRequest = 10
    for j in range(int((countRequests + sizeCoRequest - 1) / sizeCoRequest)):

        for i in range(j * sizeCoRequest, min((j + 1) * sizeCoRequest, countRequests)):
            for bucket, client in ((LUNA_IMAGE_STORE_PORTRAITS_BUCKET, STORE_PORTRAITS_CLIENT),
                                   (LUNA_IMAGE_STORE_WARPED_IMAGES_BUCKET, STORE_WARPS_CLIENT)):
                yield client.deleteImages(bucket, imageIds[1000 * i: 1000 * (i + 1)], raiseError=False)


class GCDescriptorsWorker:
    """
    Worker for removing non linked faces of account.

    Attributes:
        logger: logger
        task: task for processing
        requestId (str): luna request id
    """
    def __init__(self, logger: Logger, task: Task, requestId: Optional[str] = None) -> None:
        self.logger = logger
        self.task = task
        self.requestId = getRequestId(requestId)
        self.dbAdminContext = DBContext(self.logger)

    @gen.coroutine
    def putErrorAndSendTaskErrorStats(self, errorRes: ErrorInfo) -> Generator[None, None, None]:
        """
        Put task error to database and send stats

        Args:
            errorRes: task error
        """
        self.logger.error(errorRes.description)
        self.dbAdminContext.putError(self.task.id, errorRes.errorCode, errorRes.description)
        yield sendGCListsStats((errorRes.description, errorRes.errorCode, self.task.target),
                               StatsType.ERRORS, self.logger)

    @gen.coroutine
    def sendGCDescriptorsStats(self, countRemovingFaces: int, countLunaImageStoreRemoveImages: int,
                               startTaskTime: float) -> Generator[None, None, None]:
        """
        Send long_tasks descriptors stats.

        Args:
            countRemovingFaces: count removing faces
            countLunaImageStoreRemoveImages: count removing portraits
            startTaskTime: start of task
        """
        self.logger.debug("removing old descriptors count: " + str(countRemovingFaces))
        yield sendGCListsStats(
            (self.task.target, countRemovingFaces, countLunaImageStoreRemoveImages, time() - startTaskTime),
            StatsType.TASK_STATS, self.logger)

    @timer
    @gen.coroutine
    def gcDescriptors(self) -> Generator[None, None, None]:
        """
        Remove non linked faces of account.
        """
        startTime = time()

        try:
            gcInfo = {"count_s3_errors": 0, "count_delete_descriptors": 0}
            if self.dbAdminContext.getTask(self.task.id).done is not None:
                return

            @gen.coroutine
            def removeFromLuna(descriptors):
                yield removeDescriptorsFromLuna(descriptors, self.logger, self.requestId)

            @gen.coroutine
            def removeFromLunaImageStore(descriptors):
                yield removePortraitsAndWarpsFromLunaImageStore(descriptors)

            actions = [removeFromLuna, removeFromLunaImageStore]

            lastUpdateLt = (datetime.datetime.today() - datetime.timedelta(days=1)).isoformat() + "Z"
            for i in range(1000000):
                response = yield FACES_CLIENT.removeNotLinkedFaces(timeLt=lastUpdateLt, accountId=self.task.target,
                                                                   raiseError=True, lunaRequestId=self.requestId)
                removedDescriptors = response.json["face_ids"]
                gcInfo["count_delete_descriptors"] += len(removedDescriptors)

                for action in actions:
                    if self.dbAdminContext.getTask(self.task.id).done is not None:
                        return
                    yield action(removedDescriptors)

                if len(removedDescriptors) == 0:
                    yield self.sendGCDescriptorsStats(gcInfo["count_delete_descriptors"], 0, startTime)
                    self.dbAdminContext.patchTask(self.task.id, gcInfo)
                    return
        except VLException as e:
            self.logger.exception()
            yield self.putErrorAndSendTaskErrorStats(e.error)
        except LunaApiException as e:
            error = generateLunaCoreRequestError(e, self.logger)
            yield self.putErrorAndSendTaskErrorStats(error)

    @gen.coroutine
    def startGCNonLinkedFacesOfAccount(self) -> Generator[None, None, None]:
        """
        Start removing non linked faces of account
        """
        yield self.gcDescriptors()
        self.dbAdminContext.finishPartOfTask(self.task.id)
        self.logger.info("task {}, subtask {} done".format(self.task.id, self.task.subtask))
