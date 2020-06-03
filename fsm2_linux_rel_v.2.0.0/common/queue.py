from tornado.queues import Queue
from tornado import gen
from tornado.ioloop import IOLoop


class Consumer:
    """
    Base queue worker class.

    Attributes:
        id (int): the consumer id
        queue (Queue): the consumer queue
        logger (Logger): logger to log errors if occurred
    """
    id = 0

    def __init__(self, queue, logger):
        """
        :param queue: queue to take tasks from
        :param logger: logger to log errors if occurred
        """
        Consumer.id += 1
        self.id = Consumer.id
        self.queue = queue
        self.logger = logger

    @gen.coroutine
    def process(self):
        """
        Endless task procedure.

        :return: None
        """
        while True:
            obj = yield self.queue.get()
            try:
                yield self.f(obj)
            except Exception:
                try:
                    self.logger.exception()
                except Exception:
                    self.logger.error("failed logged exception")
            finally:
                self.queue.task_done()

    @gen.coroutine
    def f(self, *args, **kwargs):
        """
        Am abstract function to call for every object in the queue..

        :param args:
        :param kwargs:
        """
        raise NotImplementedError


class BaseQueue:
    """
    Base queue class.

    Attributes:
        queue (Queue): the Queue instance
        consumers (list): consumers
        start (bool): if queue is started
        countConsumer (int): the maximum consumer count
        consumerCls (type): the queue consumer constructor
        logger (Logger): logger to log errors if occurred
    """
    def __init__(self, consumerCls, countConsumer, logger):
        """
        :param consumerCls: The queue consumer constructor.
        :param countConsumer: The maximum consumer count.
        :param logger: logger to log errors if occurred
        """
        self.queue = Queue()
        self.consumers = []
        self.start = False
        self.countConsumer = countConsumer
        self.consumerCls = consumerCls
        self.logger = logger

    @gen.coroutine
    def putTask(self, task):
        """
        Add a task to the queue. Start consumers if not started yet.

        :param task: a task to add to the queue
        :return: None
        """

        if not self.start:
            for i in range(self.countConsumer):
                consumer = self.consumerCls(self.queue, self.logger)
                self.consumers.append(consumer)
                IOLoop.current().spawn_callback(consumer.process)
            self.start = True

        yield self.queue.put(task)
