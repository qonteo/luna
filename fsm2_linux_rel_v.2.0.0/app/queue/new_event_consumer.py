from common.queue import BaseQueue, Consumer
from tornado import gen
from app.common_objects import logger
from app.handlers.websocket_handler import EventWebSocketHandler
from app.common_objects import ES_CLIENT as es
from app.common_objects import timer


class WSNewEventWorker(Consumer):
    """
    WebSocket new event worker.
    """
    @timer.timerTor
    @gen.coroutine
    def f(self, event):
        self.logger.debug("Start ws event, event {}".format(event.id))
        yield EventWebSocketHandler.writeMassage(event)


NEW_GROUP_WS_QUEUE = BaseQueue(WSNewEventWorker, 5, logger)


class ESSaveEventWorker(Consumer):
    """
    ES new event worker.
    """
    @timer.timerTor
    @gen.coroutine
    def f(self, event):
        """
        Worker function.

        :param event: event to save
        :return: None
        """
        self.logger.debug("Start execute event policy, group {}".format(event.id))
        yield NEW_GROUP_WS_QUEUE.putTask(event)
        res = yield es.putEvent(event)
        self.logger.debug("End execute {}, {}".format(event.id, res.description))


SAVE_NEW_EVENT_QUEUE = BaseQueue(ESSaveEventWorker, 5, logger)
