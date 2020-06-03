"""
Module realize a worker for setting and monitoring reload tasks in daemons.
"""
from typing import Generator, List

from luna3.common.exceptions import LunaApiException
from luna3.faces.faces import FacesApi
from tornado import gen, ioloop

from configs.config import LUNA_MATCHER_DAEMONS, LUNA_FACES_ORIGIN, LUNA_FACES_API_VERSION, \
    MIN_FACES_IN_LIST_FOR_INDEXING, INDEXED_FACES_LISTS, REQUEST_TIMEOUT, CONNECT_TIMEOUT
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.utils.log import Logger
from crutches_on_wheels.utils.rid import generateRequestId
from crutches_on_wheels.utils.timer import timer
from db.context import ALL_LISTS
from workers.daemons_api import DaemonContext
from workers.task import IndexTask
import ujson as json


class ReloadWorker:
    """
    Worker for reloading index on daemons.

    Worker restarts daemons' matchers sequentially. After sending restart matchers task to a daemon, the worker
    monitors it.
    If one or more matchers were restarted successfully, state will be set to 0 (success).

    Attributes:
        task (IndexTask): current task
        logger (Logger): logger
    """

    def __init__(self, task: IndexTask):
        self.task = task
        self.logger = task.logger
        self.daemonContext = DaemonContext(self.logger)

    @timer
    @gen.coroutine
    def getGenerationForRestart(self, forceReload: bool = False) -> Generator[None, None, List[str]]:
        """
        Get actual generations for restarting matchers.
        Args:
            forceReload: flag for force reload all indexes
        Returns:
            list of generations
        Raises:
            LunaApiException: if request to luna-face is failed
        """
        mapListGeneration = self.task.dbContext.getCurrentGenerations()
        if not forceReload:
            mapListGeneration[self.task.listId] = self.task.generation
        lists = list(mapListGeneration.keys())
        facesClient = FacesApi(LUNA_FACES_ORIGIN, LUNA_FACES_API_VERSION, asyncRequest=True,
                               lunaRequestId=self.task.taskRequestId,
                               connectTimeout=CONNECT_TIMEOUT, requestTimeout=REQUEST_TIMEOUT)
        for listId in lists:
            try:
                lunaList = (yield facesClient.getList(listId, pageSize=0, raiseError=True)).json
                if INDEXED_FACES_LISTS == ["all"]:
                    if lunaList["face_count"] < MIN_FACES_IN_LIST_FOR_INDEXING:
                        del mapListGeneration[listId]
                else:
                    if lunaList["list_id"] not in INDEXED_FACES_LISTS:
                        del mapListGeneration[listId]
            except LunaApiException as e:
                if e.statusCode != 404:
                    raise
                del mapListGeneration[listId]
        return list(mapListGeneration.values())

    @timer
    @gen.coroutine
    def initiateRestart(self, daemonEndPoint: str, generations: List[str]) -> Generator[None, None, str]:
        """
        Send restart matchers request to daemon

        Args:
            daemonEndPoint: the daemon endpoint
            generations: generation list
        Returns:
            task id
        """
        taskId = yield self.daemonContext.startTask(self.task, json.dumps({"indices": generations}), "restart_tasks",
                                                    daemonEndPoint)
        return taskId

    @timer
    @gen.coroutine
    def monitorRestarting(self, uploadTaskId: str, daemonEndPoint: str) -> Generator[None, None, None]:
        """
        Monitor matchers restarting process on a daemon.

        Args:
            daemonEndPoint: the daemon endpoint
            uploadTaskId: task id from daemon
        Raises:
            VLException
        """
        while True:
            state, responseJson = yield self.daemonContext.getStateOfTask(self.task, daemonEndPoint, uploadTaskId,
                                                                          "restart_tasks")
            if state not in ("Running", "Restarting"):
                if state == "Failed":
                    error = Error.formatError(Error.FailedReloadIndex, self.task.generation, daemonEndPoint,
                                              responseJson["reason"])
                else:
                    error = Error.formatError(Error.BadStatusOfRestartTask, state, daemonEndPoint, self.task.generation)
                raise VLException(error)
            elif state == "Running":
                return
            else:
                self.logger.debug("Wait to reload indexes on daemon {}".format(daemonEndPoint))
                yield gen.sleep(1)

    @timer
    @gen.coroutine
    def reloadIndexOnOneDaemon(self, daemonEndPoint, generations) -> Generator[None, None, None]:
        """
        Initiate process of reloading index on a daemon and monitor it.

        Args:
            daemonEndPoint: the daemon endpoint
            generations: generation list
        """
        self.task.logger.info("Start to reload indexes {} on daemon {}".format(generations, daemonEndPoint))
        taskId = yield self.initiateRestart(daemonEndPoint, generations)
        yield self.monitorRestarting(taskId, daemonEndPoint)
        self.task.logger.info("Indexes {} are reloaded on daemon {}".format(generations, daemonEndPoint))

    @timer
    @gen.coroutine
    def reloadIndexes(self, forceReload: bool = False) -> Generator[None, None, None]:
        """
        Reload the index on all daemons.

        Args:
            forceReload: flag for force reload all indexes
        """
        self.daemonContext = DaemonContext(self.logger)
        self.logger.info("Start reload index on daemons")
        try:
            self.task.startReloadIndex()
            generations = yield self.getGenerationForRestart(forceReload)
            self.logger.info("generation to reload: {}".format(generations))
        except VLException as e:
            self.logger.error(e.error.detail)
            self.task.fail("Failed to get generations for restarting")
            return
        except LunaApiException as e:
            self.logger.error(e.json)
            self.task.fail(str(e.json))
            return
        except Exception as e:
            self.logger.exception()
            self.task.fail("Unknown error in getting generations")
            return

        successCount = 0
        for daemonEndPoint in LUNA_MATCHER_DAEMONS:
            try:
                yield self.reloadIndexOnOneDaemon(daemonEndPoint, generations)
                successCount += 1

            except VLException as e:
                self.logger.error(e.error.detail)
            except Exception as e:
                self.logger.exception()
        self.task.finishReloadIndex()
        if successCount > 0:
            self.task.success()
            self.logger.info("Success to reload index, generations: {}".format(generations))

        else:
            self.task.fail("Failed to restart matchers on every daemons")
            self.logger.error("Failed reload index on daemons")

    @classmethod
    def forceReloadIndexes(cls) -> None:
        """
        Force reload all indexes.
        """
        requestId = generateRequestId()
        logger = Logger(requestId)
        task = IndexTask(ALL_LISTS, logger, requestId)
        worker = cls(task)
        logger.info("Start force reload")
        ioloop.IOLoop.current().run_sync(lambda: worker.reloadIndexes(forceReload=True))
        logger.info("End force reload")
