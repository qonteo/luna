"""
Module realize a worker for setting and monitoring upload tasks in daemons.
"""
from typing import Generator

from tornado import gen
from configs.config import LUNA_MATCHER_DAEMONS
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.utils.timer import timer
from workers.daemons_api import DaemonContext
from workers.task import IndexTask
from workers.worker_queues import ReloadQueue
import ujson as json


class UploadWorker:
    """
    Worker for uploading index to daemons.

    Worker set download index tasks to daemons. After that the worker monitors them.

    Attributes:
        task (IndexTask): current task
        logger (Logger): logger
        outputQueue (ReloadQueue): queue for reload index task
    """

    def __init__(self, task: IndexTask, outputQueue: ReloadQueue):
        self.task = task
        self.logger = task.logger
        self.outputQueue = outputQueue
        self.daemonContext = DaemonContext(self.logger)

    @timer
    @gen.coroutine
    def initiateDownload(self, daemonEndPoint: str) -> Generator[None, None, str]:
        """
        Send upload index request to daemon

        Args:
            daemonEndPoint: the daemon endpoint
        Returns:
            task id
        """
        taskId = yield self.daemonContext.startTask(self.task, json.dumps({"index": self.task.generation}), "upload_tasks", daemonEndPoint)
        return taskId

    @timer
    @gen.coroutine
    def monitorDownloading(self, uploadTaskId: str, daemonEndPoint: str) -> Generator[None, None, None]:
        """
        Monitor index downloading process on a daemon.

        Args:
            daemonEndPoint: the daemon endpoint
            uploadTaskId: task id from daemon
        Raises:
            VLException
        """
        while True:
            state, responseJson = yield self.daemonContext.getStateOfTask(self.task, daemonEndPoint, uploadTaskId, "upload_tasks")
            if state not in ("Done", "InProgress"):
                if state == "Failed":
                    error = Error.formatError(Error.FailedUploadIndex, self.task.generation, daemonEndPoint, responseJson["reason"])
                else:
                    error = Error.formatError(Error.BadStatusOfUploadTask, state, daemonEndPoint, self.task.generation)
                raise VLException(error)
            elif state == "Done":
                return
            else:
                self.logger.debug("Wait to upload index {} on daemon {}".format(self.task.generation, daemonEndPoint))
                yield gen.sleep(1)

    @timer
    @gen.coroutine
    def uploadIndexToOneDaemon(self, daemonEndPoint) -> Generator[None, None, None]:
        """
        Initiate process of uploading index on a daemon and monitor in.

        Args:
            daemonEndPoint: the daemon endpoint
        """
        self.task.logger.info("Start to upload index to daemon {}".format(daemonEndPoint))
        taskId = yield self.initiateDownload(daemonEndPoint)
        yield self.monitorDownloading(taskId, daemonEndPoint)
        self.task.logger.info("Index {} is uploaded to daemon {}".format(self.task.generation, daemonEndPoint))

    @timer
    @gen.coroutine
    def uploadIndex(self) -> Generator[None, None, None]:
        """
        Upload index to all workers.
        """
        try:
            self.daemonContext = DaemonContext(self.logger)
            self.task.logger.info("Start upload index to daemons")
            self.task.startUploadIndex()
            yield [self.uploadIndexToOneDaemon(daemonEndPoint) for daemonEndPoint in LUNA_MATCHER_DAEMONS]
            yield self.outputQueue.putTask(self.task)
            self.task.logger.info("Index is uploaded to all daemons")
        except VLException as e:
            self.task.fail(e.error.detail)
            self.logger.error(e.error.detail)
        except Exception as e:
            self.logger.exception()
            self.task.fail("Uncaught exception in upload index worker")
        try:
            self.task.finishUploadIndex()
        except Exception as e:
            self.logger.exception()
