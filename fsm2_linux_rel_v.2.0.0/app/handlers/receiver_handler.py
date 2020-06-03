import base64

from tornado import web, gen
from wand.image import Image

from app.classes.events import InputEvent
from app.classes.fsm_handlers import HandlerManager
from app.handlers.base_handler import BaseHandler, coRequestExeptionWrap
from common.helpers import replaceTimeRecursively
from errors.error import Error, Result
from app.common_objects import timer


def checkFormatAndConvertImage(byteImg):
    """
    Check format mimetype and convert the input image if format is not ["image/jpg", "image/jpeg", " image/pjpeg"].

    :param byteImg: image bytes.
    :return: converted image bytes.
    """
    with Image(blob = byteImg) as img:
        if not (img.mimetype in ["image/jpg", "image/jpeg", " image/pjpeg"]):
            img.format = 'jpg'
            return img.make_blob()
        else:
            return byteImg


class ReceiverHandler(BaseHandler):
    """
    Image receiver handler.
    """
    def getEventImg(self):
        """
        Decode image from base64 if needed and convert to the jpg format.

        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        contentType = self.request.headers.get("Content-Type", None)
        if contentType not in ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff',
                               'image/gif', 'image/x-portable-pixmap', 'image/x-bmp-base64',
                               'image/x-jpeg-base64', 'image/x-png-base64', 'image/x-tiff-base64',
                               'image/x-gif-base64', 'image/x-portable-pixmap-base64']:
            error = Error.BadContentType
            return Result(error, 415)

        if contentType in ['image/x-bmp-base64', 'image/x-jpeg-base64', 'image/x-png-base64', 'image/x-tiff-base64',
                           'image/x-gif-base64', 'image/x-portable-pixmap-base64']:
            try:
                if contentType == 'image/x-portable-pixmap-base64':
                    contentType = 'image/x-portable-pixmap'
                else:
                    partsContentType = contentType.split("/")
                    baseType = partsContentType[1]
                    newBaseType = '-'.join(baseType.split('-')[1:-1])
                    contentType = partsContentType[0] + "/" + newBaseType
                body = base64.b64decode(self.request.body)
            except ValueError:
                error = Error.ConvertBase64Error
                return Result(error, 400)

        else:
            body = self.request.body

        if contentType in ("image/png", "image/x-portable-pixmap", "image/bmp", "image/tiff", "image/gif",
                           "image/x-windows-bmp"):
            try:
                body = checkFormatAndConvertImage(body)
            except Exception:
                error = Error.ConvertImageToJPGError
                return Result(error, 400)

        return Result(Error.Success, body)

    def initialize(self):
        """
        Set self.events an empty list.

        :return: None
        """
        self.events = []

    def prepare(self):
        """
        Create an inputEvent from request data.

        :return: None
        """
        if self.request.method == "OPTIONS":
            return

        imgRes = self.getEventImg()
        if imgRes.fail:
            return self.error(imgRes.value, imgRes.errorCode, imgRes.description)

        binaryImg = imgRes.value

        self.event = InputEvent(binaryImg)
        self.event.warped_img = bool(int(self.get_query_argument("warped_image", 0)))
        self.event.external_id = self.get_query_argument("external_id", None)
        tagsStr = self.get_query_argument("tags", None)
        if tagsStr is not None:
            self.event.tags = tagsStr.split(",")

        self.event.source = self.get_query_argument("source", None)
        self.event.user_data = self.get_query_argument("user_data", "")

    @property
    def event(self):
        """
        Input event getter.

        :return: inputEvent
        """
        return self.inputEvent

    @event.setter
    def event(self, value):
        """
        Input event setter.

        :param value: inputEvent to save as self.inputEvent
        :return: None
        """
        self.inputEvent = value

    @web.asynchronous
    @timer.timerTor
    @coRequestExeptionWrap
    @gen.coroutine
    def post(self, handlerId):
        """
        Receiver handler.
        Response status codes:
            201 if request processed successfully
            400 if request query parameters have wrong values
            404 if a handler was not found by the id
            500 if internal system error occurred

        :param handlerId: the handler id to get event processing policy from
        :return: None
        """
        handlerRes = yield HandlerManager.getHandler(handlerId)
        if handlerRes.fail:
            if handlerRes.error == Error.HandlerNotFound:
                return self.error(404, handlerRes.errorCode, handlerRes.description)
            return self.error(500, handlerRes.errorCode, handlerRes.description)

        handler = handlerRes.value
        self.event.handler_id = handlerId
        processRes = yield handler.process(self.event)

        if processRes.fail:
            yield self.event.save()
            if processRes.error == Error.MultipleFacesError:
                description = {
                    "description": processRes.description,
                    "event_id": self.event.id,
                    "faces": processRes.value,
                }
                return self.error(400, processRes.errorCode, description)
            return self.error(processRes.value, processRes.errorCode, processRes.description)
        else:
            if handler.type == "search":
                self.events = [processRes.value]
            else:
                self.events = processRes.value

        saveEventsFutures = []
        for event in self.events:
            saveEventsFutures.append(event.save())

        for saveEventFuture in saveEventsFutures:
            res = yield saveEventFuture
            if res.fail:
                return self.error(500, res.errorCode, res.description)

        events = [replaceTimeRecursively(event.dictForJson) for event in self.events]
        return self.success(201, {"events": events, "total": len(events)})
