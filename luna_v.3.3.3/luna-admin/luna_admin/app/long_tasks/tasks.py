"""
Module send reextract tasks to workers
"""
import ujson as json
from typing import Generator, List, Union, Optional
from luna3.common.exceptions import LunaApiException
from crutches_on_wheels.utils.log import Logger
from app.admin_db.db_context import DBContext as AdminDBContext, TaskType
from app.api_db.db_function import DBContext as ApiDBContext
from tornado import gen, httpclient
from tornado.httpclient import HTTPRequest
from common.api_clients import FACES_CLIENT, CORE_REEXTRACT_CLIENT
from crutches_on_wheels.errors.errors import Error, ErrorInfo
from configs.config import BATCH_SIZE, MAX_DESCRIPTOR_COUNT_ONE_REEXTRACT_ITERATION, ADMIN_TASKS_SERVER_ORIGIN, \
    REQUEST_TIMEOUT, CONNECT_TIMEOUT
from crutches_on_wheels.errors.exception import VLException
from app.utils.functions import getRequestId


@gen.coroutine
def sendTaskToWorker(dbAdminContext: AdminDBContext, taskId: int, subTask: int, target: Union[str, list],
                     taskType: int, requestId: Optional[str] = None) -> Generator[None, None, None]:
    """

    Args:
        dbAdminContext: db context
        taskId: task id
        subTask: subtask number
        target: target (descriptors list or account id)
        taskType: task type
        requestId: luna request id
    """
    requestId = getRequestId(requestId)
    logger = Logger(requestId)
    client = httpclient.AsyncHTTPClient()
    payload = {"task_id": taskId,
               "subtask": subTask,
               "target": target,
               "task_type": taskType}
    request = HTTPRequest('{}/task'.format(ADMIN_TASKS_SERVER_ORIGIN),
                          method="POST",
                          request_timeout=REQUEST_TIMEOUT,
                          connect_timeout=CONNECT_TIMEOUT,
                          headers={"Content-Type": "application/json", "LUNA-Request-Id": requestId},
                          body=json.dumps(payload))
    reply = yield client.fetch(request, raise_error=False)
    if reply.code != 201:
        logger.error("failed request to task server")
        if reply.code != 599:
            errorJson = json.loads(reply.body)
            if "error_code" in errorJson:
                logger.error(errorJson)
                error = Error.getErrorByErrorCode(errorJson["error_code"])
            else:
                error = Error.UnknownError
        else:
            error = Error.RequestToTaskServerTornadoError
        dbAdminContext.putError(taskId, error.errorCode,
                                error.description)
        dbAdminContext.finishTask(taskId, False)


class GCNonLinkedFacesTask:
    """
    Attributes:
        dbAdminContext: db context
        taskId (int): task id
        target (str): all or account id
        targetId (Union[str, None]):  account id for corresponding task
        senderToExecute (callable): function which send task to workers.
    """

    def __init__(self, dbAdminContext: AdminDBContext, dbApiContext: ApiDBContext, target="all", targetId=None,
                 requestId: Optional[str] = None):
        self.dbAdminContext = dbAdminContext
        self.dbApiContext = dbApiContext
        self.target = target
        self.targetId = targetId
        self.requestId = getRequestId(requestId)
        self.logger = Logger(self.requestId)
        if self.target == "all":
            self.taskId = dbAdminContext.createTask(TaskType.descriptorsGC, "all")
            self.kwargs = {"taskId": self.taskId}
            self.senderToExecute = self.gcAllAccountsDescriptors
        else:
            self.taskId = dbAdminContext.createTask(TaskType.descriptorsGC, "account " + self.targetId)
            self.kwargs = {"taskId": self.taskId, "accountId": self.targetId}
            self.senderToExecute = self.gcAccountFaces

    @gen.coroutine
    def gcAccountFaces(self, taskId, accountId) -> Generator[None, None, None]:
        """
        Send task of removal non linked account faces to workers.

        Set part count of task to 1 and send task to workers.

        Args:
            taskId: task id
            accountId: account id
        """
        self.dbAdminContext.setCountOfParts(taskId, 1)
        yield sendTaskToWorker(self.dbAdminContext, taskId, 1, accountId, TaskType.descriptorsGC.value, self.requestId)

    @gen.coroutine
    def gcAllAccountsDescriptors(self, taskId) -> Generator[None, None, None]:
        """
        Send tasks of removal non linked faces of all accounts to workers. For every account one task.

        Set part count of task to len(accounts) and send task to workers.

        Args:
            taskId: task id
        """
        try:
            try:
                accountsIds = self.dbApiContext.getAllAccounts()
            except VLException as e:
                self.logger.exception("failed get accountsId, task {}".format(taskId))
                self.dbAdminContext.putError(taskId, e.error.errorCode, e.error.description)
                self.dbAdminContext.finishTaskIfNeed(taskId, False)
                return

            self.dbAdminContext.setCountOfParts(taskId, len(accountsIds))
            if len(accountsIds) == 0:
                self.dbAdminContext.finishTask(taskId)
                return

            for count, accountId in enumerate(accountsIds):
                yield sendTaskToWorker(self.dbAdminContext, taskId, count, accountId, TaskType.descriptorsGC.value,
                                       self.requestId)

        except Exception:
            self.logger.exception()
            self.logger.exception("failed execute task {}".format(taskId))
            self.dbAdminContext.putError(taskId, Error.UnknownError.errorCode, Error.UnknownError.description)
            self.dbAdminContext.finishTaskIfNeed(taskId, False)


class ReExtractTask:
    """
    Reextract task

    Attributes:
        dbAdminContext: db context
        descriptors: descriptors
        target: all or account id
        requestId: luna request id
    """

    def __init__(self, dbAdminContext: AdminDBContext, descriptors=None, target="all", requestId: Optional[str] = None):
        self.taskId = dbAdminContext.createTask(TaskType.reExtractGC, target)
        self.kwargs = {"taskId": self.taskId}
        self.requestId = getRequestId(requestId)
        self.logger = Logger(self.requestId)
        self.descriptors = descriptors
        self.dbAdminContext = dbAdminContext
        if descriptors is not None:
            self.kwargs["descriptors"] = self.descriptors

    @gen.coroutine
    def prepareReExtractAllDescriptors(self, taskId) -> Generator[None, None, bool]:
        """
        Test connection to new core and set task parts count.

        Args:
            taskId: task id

        Returns:
            True if success otherwise false.
        """

        try:
            yield self.testConnectionToNewCore()

            descriptorCount = (yield FACES_CLIENT.getAttributesIds(raiseError=True,
                                                                   lunaRequestId=self.requestId)).json["count"]
            self.dbAdminContext.setCountOfParts(taskId, (descriptorCount + BATCH_SIZE - 1) // BATCH_SIZE)
        except VLException as e:
            error = e.error
            self.logger.exception()
        except LunaApiException as e:
            error = ErrorInfo(e.json["error_code"], e.json["detail"])
            self.logger.exception()
        except Exception:
            self.logger.exception()
            error = Error.UnknownError
        else:
            self.logger.debug("success send task {} to workers".format(taskId))
            return True
        self.logger.error("failed execute task {}".format(taskId))
        self.dbAdminContext.putError(taskId, error.errorCode, error.description)
        self.dbAdminContext.finishTask(taskId, False)
        return False


    @gen.coroutine
    def reExtractAllDescriptorAttribute(self, taskId: int) -> Generator[None, None, None]:
        """
        Send to re-extract all descriptors tasks to workers. For every account one task.

        All descriptors are split into chunks. Every chunk - one sub task.
        Set part count of task to len(accounts) and send task to workers.

        Args:
            taskId: task id
        """
        MAX_ITERATION_COUNT = 10 ** 9

        self.logger.info("start re-extract descriptors, {}".format(taskId))
        if not (yield self.prepareReExtractAllDescriptors(taskId)):
            return

        for i in range(1, MAX_ITERATION_COUNT):
            response = yield FACES_CLIENT.getAttributesIds(pageSize=MAX_DESCRIPTOR_COUNT_ONE_REEXTRACT_ITERATION,
                                                           page=i, raiseError=True, lunaRequestId=self.requestId)

            yield sendTaskToWorker(self.dbAdminContext, taskId, i, response.json["attributes"],
                                   TaskType.reExtractGC.value, self.requestId)
            if response.json["count"] <= MAX_DESCRIPTOR_COUNT_ONE_REEXTRACT_ITERATION * i:
                break
        else:
            self.dbAdminContext.putError(taskId, Error.ReExtractExceedMaximumIteration.errorCode,
                                         Error.ReExtractExceedMaximumIteration.description)
            self.dbAdminContext.finishTask(taskId, False)

    @gen.coroutine
    def testConnectionToNewCore(self) -> Generator[None, None, None]:
        """
        Test Connection to new core.

        Raises:
            VLException(Error.CheckConnectionToReExtractBroker, 500): if check is failed
        """
        success = yield CORE_REEXTRACT_CLIENT.testConnection(asyncRequest=True, lunaRequestId=self.requestId)
        if not success:
            raise VLException(Error.CheckConnectionToReExtractBroker, 500)

    @gen.coroutine
    def reExtractDescriptorsList(self, taskId: int, attributesIds: List[str]) -> Generator[None, None, None]:
        """
        Send tasks of descriptors re-extract to workers. For every account one task.

        All descriptors separate by chunk. Every chunk - one sub task.
        Set part count of task to len(accounts) and send task to workers.

        Args:
            taskId: task id
            attributesIds: list of attributes ids. New descriptors are parts these attributes.
        """
        try:
            self.logger.info("start re-extract descriptors, {}".format(taskId))
            descriptorsCount = len(attributesIds)

            yield self.testConnectionToNewCore()



            def getPageCount(objCount, pageSize):
                return (objCount + pageSize - 1) // pageSize

            self.dbAdminContext.setCountOfParts(taskId, getPageCount(descriptorsCount, BATCH_SIZE))
            maxDescriptorsCount = MAX_DESCRIPTOR_COUNT_ONE_REEXTRACT_ITERATION

            for i in range(getPageCount(descriptorsCount, maxDescriptorsCount)):
                yield sendTaskToWorker(self.dbAdminContext, taskId, i,
                                       attributesIds[i * maxDescriptorsCount: (i + 1) * maxDescriptorsCount],
                                       TaskType.reExtractGC.value, self.requestId)

        except VLException as e:
            error = e.error
            self.logger.exception()
        except LunaApiException as e:
            error = ErrorInfo(e.json["error_code"], e.json["detail"])
            self.logger.exception()
        except Exception:
            self.logger.exception()
            error = Error.UnknownError
        else:
            self.logger.debug("success send task {} to workers".format(taskId))
            return
        self.logger.error("failed execute task {}".format(taskId))
        self.dbAdminContext.putError(taskId, error.errorCode, error.description)
        self.dbAdminContext.finishTask(taskId, False)
