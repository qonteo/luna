"""
Module realize queues for internal use.
"""
from tornado import gen
from tornado.queues import Queue

from workers.index_reload_worker import ReloadWorker


class ReloadQueue:
    """
    Reload daemon-matchers queue class.

    Attributes:
        queue (Queue): the Queue instance
    """

    def __init__(self):
        self.queue = Queue()

    @gen.coroutine
    def putTask(self, task):
        """
        Add a task to the queue. Start consumers if not started yet.

        Args:

            task: a task to add to the queue
        """

        yield self.queue.put(task)

    @gen.coroutine
    def process(self):
        while True:
            task = yield self.queue.get()
            worker = ReloadWorker(task)
            try:
                yield worker.reloadIndexes()
            except Exception:
                task.logger.exception()
            finally:
                self.queue.task_done()
