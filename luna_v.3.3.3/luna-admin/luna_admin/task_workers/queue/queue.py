from tornado import gen
from tornado.ioloop import IOLoop
from tornado.queues import Queue
from logbook import Logger
from app.admin_db.db_context import DBContext as AdminDBContext
from crutches_on_wheels.errors.errors import Error
from task_workers.worker_task import Task
from typing import Generator, Callable, Optional
from crutches_on_wheels.utils.log import Logger


class Consumer:
    """
    Base queue worker class.

    Attributes:
        id (int): the consumer id
        queue (Queue): the consumer queue
        logger (Logger): logger to log errors if occurred
        dbAdminContext (DBContext): db context
        requestId (str): luna request id
    """
    id = 0

    def __init__(self, queue: Queue, requestId: Optional[str] = None) -> None:
        """
        Args:
            queue: queue to take tasks from
        """
        Consumer.id += 1
        self.id = Consumer.id
        self.queue = queue
        self.logger = Logger(requestId)
        self.dbAdminContext = AdminDBContext(self.logger)

    @gen.coroutine
    def process(self) -> None:
        """
        Endless task procedure.
        Returns:
            None
        """
        while True:
            obj = yield self.queue.get()
            try:
                yield self.f(obj)
            except Exception:
                self.logger.exception()
            finally:
                self.queue.task_done()

    @gen.coroutine
    def f(self, *args, **kwargs) -> None:
        """
        Am abstract function to call for every object in the queue..
        Args:
            args
            kwargs
        Raises:
            NotImplementedError
        """
        raise NotImplementedError

    def uncaughtException(self, taskId: int, subtask: int) -> None:
        """
        Put error and finish task if uncaught exception
        Args:
            taskId: task id
            subtask: sub task
        """
        self.logger.error(
            "Uncaught exception in reextract worker, task cancelled, task {}, subtask {}".format(taskId, subtask))
        self.logger.exception()
        error = Error.UnknownError
        self.dbAdminContext.putError(taskId, error.errorCode, error.description)
        self.dbAdminContext.finishTask(taskId, False)


class BaseQueue:
    """
    Base queue class.

    Attributes:
        queue (Queue): the Queue instance
        consumers (list): consumers
        start (bool): if queue is started
        countConsumer (int): the maximum consumer count
        consumerCls (type): the queue consumer constructor
    """

    def __init__(self, consumerCls: Callable, countConsumer: int):
        self.queue = Queue()
        self.consumers = []
        self.start = False
        self.countConsumer = countConsumer
        self.consumerCls = consumerCls

    @gen.coroutine
    def putTask(self, task: Task) -> Generator[None, None, None]:
        """
        Add a task to the queue. Start consumers if not started yet.

        :param task: a task to add to the queue
        :return: None
        """

        if not self.start:
            for i in range(self.countConsumer):
                consumer = self.consumerCls(self.queue, task.taskRequestId)
                self.consumers.append(consumer)
                IOLoop.current().spawn_callback(consumer.process)
            self.start = True

        yield self.queue.put(task)
