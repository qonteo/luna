"""
Module realize queues and consumers for long tasks.

Attributes:
    DESCRIPTOR_GC_QUEUE: queue of  gc non linked faces tasks
    REEXTRACT_QUEUE: queue of re-extract tasks
"""
from typing import Generator
from luna_admin.task_workers.queue.queue import BaseQueue, Consumer
from tornado import gen
from crutches_on_wheels.utils.timer import timer
from crutches_on_wheels.utils.log import Logger
from luna_admin.task_workers.workers.reextract_worker import ReextractWorker, PrepareStatus
from task_workers.worker_task import Task
from task_workers.workers.descriptors_worker import GCDescriptorsWorker


class DescriptorsGCConsumer(Consumer):
    """
    Worker for task of collection of non attached old descriptors of an account
    """

    @timer
    @gen.coroutine
    def f(self, task: Task) -> Generator[None, None, None]:
        """
        Worker function.

        Args:
            task: remove not attached account faces task
        """
        try:
            self.logger = Logger(task.taskRequestId)
            self.logger.info("start task {}, subtask {}".format(task.id, task.subtask))
            worker = GCDescriptorsWorker(self.logger, task)
            yield worker.startGCNonLinkedFacesOfAccount()
        except Exception:
            self.logger.exception()
            self.uncaughtException(task.id, task.subtask)


class ReextractConsumer(Consumer):
    """
    Worker for task of reextract descriptors
    """

    @timer
    @gen.coroutine
    def f(self, task) -> Generator[None, None, None]:
        """
        Worker function.

        Args:
             task for re-extract descriptors list
        """
        try:
            self.logger = Logger(task.taskRequestId)
            self.logger.info("start task {}, subtask {}".format(task.id, task.subtask))
            worker = ReextractWorker(self.logger, task)
            prepareStatus = yield worker.prepare()
            if prepareStatus != PrepareStatus.READY:
                return
            yield worker.startReExtract()
        except Exception:
            self.uncaughtException(task.id, task.subtask)


DESCRIPTOR_GC_QUEUE = BaseQueue(DescriptorsGCConsumer, 5)
REEXTRACT_QUEUE = BaseQueue(ReextractConsumer, 5)
