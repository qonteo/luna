from tornado.queues import Queue
from tornado import gen
from tornado.ioloop import IOLoop
from preview.previewer import Previewer


class PreviewConsumer:
    id = 0

    def __init__(self, queue):
        PreviewConsumer.id += 1
        self.id = PreviewConsumer.id
        self.queue = queue

    @gen.coroutine
    def process(self):
        while True:
            task = yield self.queue.get()
            image, imageId, bucket, logger = task
            previewer = Previewer(image, imageId, bucket, logger)
            try:
                yield previewer.makeThumbnails()
            except Exception:
                try:
                    logger.exception()
                except Exception:
                    logger.error("failed logged exception")
            finally:
                self.queue.task_done()



class BaseQueue:
    def __init__(self, consumerCls, countConsumer):
        self.queue = Queue()
        self.consumers = []
        self.start = False
        self.countConsumer = countConsumer
        self.consumerCls = consumerCls

    @gen.coroutine
    def putTask(self, task):

        if not self.start:
            for i in range(self.countConsumer):
                consumer = self.consumerCls(self.queue)
                self.consumers.append(consumer)
                IOLoop.current().spawn_callback(consumer.process)
            self.start = True

        yield self.queue.put(task)


THUMBNAIL_QUEUE = BaseQueue(PreviewConsumer, 5)