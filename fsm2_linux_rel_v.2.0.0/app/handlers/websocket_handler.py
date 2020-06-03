from tornado import websocket, gen
import ujson

from app.common_objects import logger, ES_CLIENT as es
from common.helpers import convertTimestampMillisToRfc3339, replaceTimeRecursively
from errors.error import Result, Error


class EventWebSocketHandler(websocket.WebSocketHandler):
    """
    Event websocket handler.
    """
    openWebSockets = []

    def check_origin(self, origin):
        """
        CORS stub.

        :param origin: origin
        :return: True
        """
        return True

    @gen.coroutine
    def open(self, handlerId):
        """
        Open WebSocket handler.

        :param handlerId: handler id to connect to
        :return: None
        """
        logger.debug("open ws connection for events")

        if handlerId is None:
            return self.close(400, "Query parameter 'handler' not found")
        if self in [socket["socket"] for socket in EventWebSocketHandler.openWebSockets]:
            return
        handlerRes = yield es.getHandler(handlerId)
        if handlerRes.fail:
            return self.close(500,
                              "Error code :{}; detail: {}".format(handlerRes.errorCode,
                                                                  handlerRes.description))
        EventWebSocketHandler.openWebSockets.append({"handler": handlerId, "socket": self})

    def on_close(self):
        """
        Close WebSocket handler.

        :return: None
        """
        EventWebSocketHandler.openWebSockets = [s for s in EventWebSocketHandler.openWebSockets if s["socket"] != self]

    @classmethod
    @gen.coroutine
    def writeMassage(cls, event):
        """
        Write message handler.

        :param event: event to send
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        countSubscribers = 0
        for socket in EventWebSocketHandler.openWebSockets:
            if socket["handler"] == event.handler_id:
                eventToWrite = event.dictForJson
                eventToWrite = ujson.dumps(replaceTimeRecursively(eventToWrite))
                socket["socket"].write_message(eventToWrite)
                countSubscribers += 1

        logger.debug("Event {} was sended {} subscribers".format(event.id, countSubscribers))
        return Result(Error.Success, 0)


class GroupWebSocketHandler(websocket.WebSocketHandler):
    """
    Group WebSocket handler.
    """
    openWebSockets = []

    def check_origin(self, origin):
        """
        CORS stub.

        :param origin: origin
        :return: True
        """
        return True

    @gen.coroutine
    def open(self, handlerId):
        """
        Open WebSocket handler.

        :param handlerId: handler id to connect to
        :return: None
        """
        logger.debug("open ws connection for groups")

        if handlerId is None:
            return self.close(400, "Query parameter 'handler' not found")
        if self in [socket["socket"] for socket in GroupWebSocketHandler.openWebSockets]:
            return
        handlerRes = yield es.getHandler(handlerId)
        if handlerRes.fail:
            return self.close(500,
                              "Error code :{}; detail: {}".format(handlerRes.errorCode,
                                                                  handlerRes.description))
        GroupWebSocketHandler.openWebSockets.append({"handler": handlerId, "socket": self})

    def on_close(self):
        """
        Close WebSocket handler.
        :return: None
        """
        GroupWebSocketHandler.openWebSockets = [s for s in GroupWebSocketHandler.openWebSockets if s["socket"] != self]

    @classmethod
    @gen.coroutine
    def writeUpdateGroupMassage(cls, group):
        """
        Write update group message handler.

        :param group: group to tell about
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        countSubscribers = 0
        for socket in GroupWebSocketHandler.openWebSockets:
            if socket["handler"] == group.handler_id:
                groupToWrite = group.dictForJson
                groupToWrite = ujson.dumps(replaceTimeRecursively(groupToWrite))
                socket["socket"].write_message(groupToWrite)
                countSubscribers += 1

        logger.debug("Group {} was sended {} subscribers".format(group.id, countSubscribers))
        return Result(Error.Success, 0)

    @classmethod
    @gen.coroutine
    def writeCloseGroupMassage(cls, group):
        """
        Write close group message handler.

        :param group: group to tell about
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        countSubscribers = 0
        for socket in EventWebSocketHandler.openWebSockets:
            if socket["handler"] == group.handler_id:
                groupToWrite = group.dictForJson
                groupToWrite = ujson.dumps(replaceTimeRecursively(groupToWrite))
                socket["socket"].write_message(groupToWrite)
                countSubscribers += 1

        logger.debug("Group {} was sended {} subscribers".format(group.id, countSubscribers))
        return Result(Error.Success, 0)
