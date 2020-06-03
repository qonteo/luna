from common.queue import BaseQueue, Consumer
from tornado import gen
from app.common_objects import logger
from app.handlers.websocket_handler import GroupWebSocketHandler
from app.common_objects import ES_CLIENT as es
from app.common_objects import timer


class WSGroupUpdateWorker(Consumer):
    """
    WebSocket update group emitter.
    """
    @timer.timerTor
    @gen.coroutine
    def f(self, group):
        """
        Worker function

        :param group: group to tell about
        :return: None
        """
        self.logger.debug("Start ws group, group {}".format(group.id))
        yield GroupWebSocketHandler.writeUpdateGroupMassage(group)


GROUP_WS_QUEUE = BaseQueue(WSGroupUpdateWorker, 2, logger)


class ESGroupUpdateWorker(Consumer):
    """
    ES update group worker.
    """
    @timer.timerTor
    @gen.coroutine
    def f(self, group):
        """
        Worker function.

        :param group: group to save
        :return: None
        """
        group.processed = False
        yield GROUP_WS_QUEUE.putTask(group)
        yield es.putGroup(group)


class ESGroupCloseWorker(Consumer):
    """
    ES close group worker
    """
    @timer.timerTor
    @gen.coroutine
    def f(self, group):
        """
        Worker function.

        :param group: closed group
        :return: None
        """
        group.processed = True
        self.logger.debug("Start close group policy, group {}".format(group.id))
        res = yield group.group_policy.executePolicy(group)
        yield GROUP_WS_QUEUE.putTask(group)
        yield es.putGroup(group)
        self.logger.debug("End execute {}, {}".format(group.id, res.description))


class ESGroupUpdateIdWorker(Consumer):
    """
    ES update group id worker (if groups are merged, all events are now in a new one).
    """
    @timer.timerTor
    @gen.coroutine
    def f(self, updateInfo):
        """
        Worker function.

        :param updateInfo: two old groups
        :return: None
        """
        newGroup = updateInfo["newGroup"]
        oldGroups = updateInfo["oldGroups"]
        futures = []
        for oldGroup in oldGroups:
            for eventId in oldGroup.events:
                futures.append({"future": es.updateGroupIdInEvent(eventId.id, newGroup.id),
                                "action": "update group id",
                                "event": eventId.id})
            futures.append({"future": es.deleteGroup(oldGroup.id),
                            "action": "delete group",
                            "group": oldGroup.id})

        for future in futures:
            res = yield future["future"]
            if res.fail:
                if "event" in future:
                    self.logger.error("fail {}, event: {}, group: {}".format(future["action"], future["event"],
                                                                        newGroup.id))
                else:
                    self.logger.error("fail {}, group: {}".format(future["action"], future["group"]))

        self.logger.debug("remove groups: {}".format([group.id for group in oldGroups]))


GROUP_UPDATE_QUEUE = BaseQueue(ESGroupUpdateWorker, 2, logger)
GROUP_CLOSE_QUEUE = BaseQueue(ESGroupCloseWorker, 2, logger)
GROUP_UPDATE_GROUP_ID = BaseQueue(ESGroupUpdateIdWorker, 2, logger)
