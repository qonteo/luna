"""
Module realize re-extract list of descriptors.
"""
import enum
from itertools import chain
from typing import List, Generator, Optional
from logbook import Logger
from luna3.common.http_objs import Image
from tornado import gen
from app.admin_db.db_context import DBContext as AdminDBContext
from common.api_clients import STORE_WARPS_CLIENT, CORE_REEXTRACT_CLIENT
from common.luna_core_error import generateLunaCoreRequestError
from crutches_on_wheels.utils.timer import timer
from configs.config import LUNA_IMAGE_STORE_WARPED_IMAGES_BUCKET, BATCH_SIZE
from crutches_on_wheels.errors.errors import Error, ErrorInfo
from crutches_on_wheels.errors.exception import VLException
from task_workers.worker_task import Task
from app.utils.functions import getRequestId


class Descriptor:
    """
    Container for store data for re-extract descriptor.

    Attributes:
        id (str): face id (attributes id)
        warp (binary): warped image
        body  (binary): new descriptor
        tempId (str): temporary descriptor id
    """

    def __init__(self, descriptorId):
        self.id = descriptorId
        self.warp = None
        self.body = None
        self.tempId = None


def unionLists(lists: List[list]) -> list:
    """
    Union list to one list.

    Args:
        lists: lists

    Returns:
        list which contained all elements of input lists.
    """
    return list(chain(*lists))


class PrepareStatus(enum.Enum):
    """
    Status of task.
    """
    CONTINUE = 1  #: in progress
    CANCELLED = 2  #: cancelled
    DONE = 3  #: done
    FAILED = 4  #: failed
    READY = 5  #: ready (for subtask)


class ReextractWorker:
    """
    Re-extract worker.

    Worker reextract descriptors. Re-extract accepts list of descriptors ids as input. Worker performs the
    following steps:

        * get list of not reextracted yet descriptors
        * get warped images which corresponding  descriptors
        * reextract warped images in a new luna-core in the temporary storage
        * move descriptors from the temporary storage to the persistent storage

    Attributes:
        logger (Logger): task logger
        task (Task): task
        dbAdminContext (AdminDBContext): db context
        requestId (str): luna request id
    """

    def __init__(self, logger: Logger, task: Task, requestId: Optional[str] = None) -> None:
        self.requestId = getRequestId(requestId)
        self.logger = logger
        self.dbAdminContext = AdminDBContext(self.logger)
        self.task = task
        self.descriptorsForReExtract = []

    @gen.coroutine
    def putErrorToDB(self, error: ErrorInfo, taskId: int, descriptorId: str) -> None:
        """
        Put error to admin database.

        Args:
            error: error
            taskId: task id
            descriptorId: descriptor id
        """
        self.dbAdminContext.putError(taskId, error.errorCode,
                                     error.description + ", descriptor: {}".format(descriptorId))

    @gen.coroutine
    def batchExtractWarpedImages(self, descriptors: List[Descriptor],
                                 taskId: int) -> Generator[None, None, List[Descriptor]]:
        """
        Batch extract to temporary

        Args:
            descriptors: list of Descriptor which contain warps images.
            taskId: task id

        Returns:
            return descriptors if request to reextract is successed otherwise empty list
        """

        if len(descriptors) == 0:
            return []

        images = [Image(descriptor.id, body=descriptor.warp, lunaOutputDescriptorID=descriptor.id) for descriptor in
                  descriptors]
        response = yield CORE_REEXTRACT_CLIENT.extractDescriptor(images, asyncRequest=True, warpedImage=True,
                                                                 lunaRequestId=self.requestId)

        if response.statusCode == 201:
            extractResult = response.json

            for extractedImages in extractResult["succeeded_images"]:
                for descriptor in descriptors:
                    if extractedImages["file_name"] == descriptor.id:
                        descriptor.tempId = extractedImages["faces"][0]["id"]
                        break
            return descriptors
        else:
            error = generateLunaCoreRequestError(response, self.logger)
            for descriptor in descriptors:
                self.dbAdminContext.putError(taskId, error.errorCode,
                                             "descriptor: {}, detail: {}".format(descriptor.id, error.description))
            return []

    @timer
    @gen.coroutine
    def getNonReExtractingDescriptors(self, descriptors: List[str],
                                      taskId: int) -> Generator[None, None, List[str]]:
        """
        Get list is not yet reextracted descriptors by list descriptors id

        Args:
            descriptors: descriptors ids
            taskId: task id

        Returns:
            list of descriptor ids  which are not re-extrated
        """
        countWorkers = 20
        descriptorIter = iter(descriptors)

        @gen.coroutine
        def checkExistDescriptor(iterByDescriptors):

            nonExistDescriptors = []

            for descriptorId in iterByDescriptors:

                response = yield CORE_REEXTRACT_CLIENT.getDescriptor(descriptorId, asyncRequest=True,
                                                                     lunaRequestId=self.requestId)
                if response.statusCode == 200:
                    self.logger.debug("descriptor {} already re-extract".format(descriptorId))
                elif response.statusCode == 404:
                    nonExistDescriptors.append(descriptorId)
                else:
                    error = generateLunaCoreRequestError(response, self.logger)
                    self.putErrorToDB(error, taskId, descriptorId)
                    self.logger.error("failed get descriptor {}".format(descriptorId))
            return nonExistDescriptors

        nonExistDescriptorsResults = yield [checkExistDescriptor(descriptorIter) for _ in range(countWorkers)]
        descriptorsForReExtract = unionLists(nonExistDescriptorsResults)
        return descriptorsForReExtract

    @gen.coroutine
    def downloadFiles(self, descriptors: List[Descriptor], taskId: int) -> Generator[None, None, List[Descriptor]]:
        """

        Args:
            descriptors: targets for downloading
            taskId: task id


        Returns:
            descriptor list with downloaded files; notice that descriptors without downloaded files will be removed
        """

        @gen.coroutine
        def downloadFile(descriptor: Descriptor) -> Generator[None, None, None]:
            response = yield STORE_WARPS_CLIENT.getImage(LUNA_IMAGE_STORE_WARPED_IMAGES_BUCKET, descriptor.id,
                                                         lunaRequestId=self.requestId)

            if response.statusCode >= 400:
                respJson = response.json
                errorCode = respJson["error_code"]
                error = Error.getErrorByErrorCode(errorCode)
                self.logger.error(
                    "id: {}, error_code: {}, detail: {}".format(descriptor.id,
                                                                errorCode, respJson["detail"]))
                self.dbAdminContext.putError(taskId, error.errorCode,
                                             error.description + ", target id: {}".format(
                                                 descriptor.id))
                descriptors.remove(descriptor)
            else:
                descriptor.warp = response.body

        yield [downloadFile(descriptor) for descriptor in descriptors]

        return descriptors

    @gen.coroutine
    def reExtractBatchDescriptors(self, descriptorIds: List[str], taskId: int) -> Generator[None, None, int]:
        """
        Re-extract descriptors batch
        Args:
            descriptorIds: list descriptors uds
            taskId: task id

        Returns:
            reextracted descriptor count
        """
        descriptors = [Descriptor(descriptorId) for descriptorId in descriptorIds]
        descriptors = yield self.downloadFiles(descriptors, taskId)
        descriptors = yield self.batchExtractWarpedImages(descriptors, taskId)
        return len(descriptors)

    @gen.coroutine
    def patchReExtractTaskProgress(self, taskId, descriptorCount) -> None:
        """
        Patch task progress.

        Args:
            taskId: task id
            descriptorCount: reextracted descriptor count
        """
        self.dbAdminContext.finishPartOfTask(taskId, (descriptorCount + BATCH_SIZE - 1) // BATCH_SIZE)

    @gen.coroutine
    def reExtractDescriptors(self, taskId: int, descriptorGroup) -> Generator[None, None, None]:
        """
        Reextract several descriptors.

        Args:
            taskId: task id
            descriptorGroup: group of descriptors
        """
        subTaskCount = (len(descriptorGroup) + BATCH_SIZE - 1) // BATCH_SIZE
        try:
            batches = [descriptorGroup[i * BATCH_SIZE: (i + 1) * BATCH_SIZE] for i
                       in range(subTaskCount)]
            batchIter = iter(batches)

            @gen.coroutine
            def worker():
                reExtractDescriptorCounts = 0
                for batch in batchIter:
                    res = yield self.reExtractBatchDescriptors(batch, taskId)
                    reExtractDescriptorCounts += res
                return reExtractDescriptorCounts

            result = yield [worker() for _ in range(10)]

        except VLException as e:
            self.logger.exception()
            error = e.error
        except Exception:
            self.logger.exception()
            error = Error.UnknownError
        else:
            self.dbAdminContext.patchTask(taskId, content={"count_delete_descriptors": sum(result)})
            return

        self.dbAdminContext.putError(taskId, error.errorCode, error.description)
        self.dbAdminContext.finishTask(taskId, False)

    @gen.coroutine
    def prepare(self) -> Generator[None, None, PrepareStatus]:
        """
        Prepare reextract.

        Get not reextracted descriptors.

        Returns:
            prepare status
        """

        if self.dbAdminContext.getTask(self.task.id).done is False:
            self.logger.info("task {} cancelled, cancel subtask {}".format(self.task.id, self.task.subtask))
            return PrepareStatus.CANCELLED

        descriptorsForReExtract = yield self.getNonReExtractingDescriptors(self.task.target, self.task.id)

        if len(self.task.target) - len(descriptorsForReExtract) > 0:
            self.dbAdminContext.patchTask(self.task.id, content={
                "count_delete_descriptors": len(self.task.target) - len(descriptorsForReExtract)
            })

        if len(descriptorsForReExtract) == 0:
            self.logger.info("descriptor count 0, task {}, subtask {} done".format(self.task.id, self.task.subtask))
            self.patchReExtractTaskProgress(self.task.id, len(self.task.target))
            return PrepareStatus.DONE
        self.logger.info("descriptor count {}, task {},  subtask {}".format(len(descriptorsForReExtract),
                                                                            self.task.id, self.task.subtask))
        self.descriptorsForReExtract = descriptorsForReExtract
        return PrepareStatus.READY

    @gen.coroutine
    def startReExtract(self) -> Generator[None, None, None]:
        """
        Start re-extract process.
        """
        yield self.reExtractDescriptors(self.task.id, self.descriptorsForReExtract)
        self.patchReExtractTaskProgress(self.task.id, len(self.task.target))
        self.logger.info("descriptor count {}, task {}, subtask {} done".format(len(self.task.target),
                                                                                self.task.id, self.task.subtask))
