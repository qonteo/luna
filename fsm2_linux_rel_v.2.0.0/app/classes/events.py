import os
import ujson as json
import uuid

from tornado import gen

from app.common_objects import ES_CLIENT as es
from app.common_objects import logger
from app.queue.new_event_consumer import SAVE_NEW_EVENT_QUEUE
from common.helpers import getNowTimestampMillis
from configs.config import SAVE_INPUT_IMAGES
from errors.error import ErrorInfo
from errors.error import Result, Error
import copy


def getPath(eventId) -> str:
    """
    Getting path to folder with image.

    If you work in *unix system in one folder must be <50k files.

    :param eventId: id of event
    :return: return string *LOCATION + "/" + eventId[-3:] + "/"*
    """
    path = "./storage/events/" + eventId[-3:] + "/"
    return path


class Event:
    """
    Structure event.

    Attributes:
        id (UUID4): id of event. If extract (search) succeed its id is equal to descriptorId.
        descriptor_id (UUID4): descriptor id which was received from luna after descriptor extraction from image.
        persons_lists (list of UUID4): Luna API person lists the person created from descriptor has been attached to.
        descriptors_lists (list of UUID4): Luna API descriptor lists the extracted descriptor has been attached to.
        search (list): search result.
        extract (dict): extract result.
        group_id (UUID4): the group id the event is in.
        search_by_group (list): result of search by recent events.
        person_id (UUID4): the person id the extracted descriptor is in.
        tags (list of str): a tag list provided with input image.
        source (str): a source provided with the input image.
        user_data (str): a created person user_data.
        img (bytearray): the input image.
        warped_img (int): image warped flag.
        external_id (str): a external_id provided with input image, used for grouping.
        error (dict): error occurred while processing the event.
        create_time (timetamp): the event create time.
        handler_id (UUID4): the handler id to process the event.
    """
    def __init__(self):
        self.id = None
        self.descriptor_id = None
        self.descriptors_lists = []
        self.persons_lists = []
        self.search = None
        self.extract = None
        self.group_id = None
        self.search_by_group = None
        self.person_id = None
        self.tags = []
        self.img = None
        self.user_data = ""
        self.warped_img = False
        self.external_id = None
        self.source = None
        self.error = None
        self.create_time = getNowTimestampMillis()
        self.handler_id = None

    @property
    def dict(self) -> dict:
        """
        Create dict from the object.

        :return: dict.
        """
        return self.__dict__

    @property
    def dictForJson(self) -> dict:
        """
        Create a dict from the event.

        :rtype: dict
        :return: json
        """
        eventDict = self.__dict__.copy()
        del eventDict["img"]
        return eventDict

    @property
    def json(self) -> str:
        """
        Create a json from the event.

        :rtype: str
        :return: json
        """
        return json.dumps(self.dictForJson, ensure_ascii = False)

    @gen.coroutine
    def saveSourceOfEvent(self):
        """
        Save the event source image.
        """
        if self.id is None:
            self.id = str(uuid.uuid4())
        path = getPath(self.id)
        if not os.path.exists(path):
            os.makedirs(path)
        eventImgFileName = os.path.join(path, "{}.jpg".format(self.id))
        # if OS == "unix":
        #     with SafeFileIOStream(eventImgFileName) as stream:
        #         yield stream.write(self.img)
        # else:
        with open(eventImgFileName, 'wb') as f:
            f.write(self.img)

    @gen.coroutine
    def save(self):
        """
        Save the input image to the storage and save the event to ES as json.
        """
        if SAVE_INPUT_IMAGES:
            self.saveSourceOfEvent()
        saveToESRes = yield es.putEvent(self)
        if saveToESRes.success:
            yield SAVE_NEW_EVENT_QUEUE.putTask(self)
            return Result(Error.Success, 0)
        else:
            return saveToESRes

    def copy(self):
        """
        Event copy.

        :rtype: Event
        :return: copy of Event
        """
        event = Event()
        for member in self.__dict__:
            if member in event.__dict__:
                event.__dict__[member] = copy.deepcopy(self.__dict__[member])

        return event

    @property
    def needExtract(self) -> bool:
        """
        Return if we need to extract event.

        :rtype: bool
        :return: if extract is none return True else False
        """
        return self.extract is None

    def setError(self, error: ErrorInfo):
        """
        Sets self.error with {"error_code": error.getErrorCode(), "detail": error.getErrorDescription()}.

        :param error: ErrorInfo
        :return: None
        """
        logger.debug("Error in event {}, error_code: {}, detail {}".format(self.id, error.getErrorCode(),
                                                                           error.getErrorDescription()))
        self.error = {"error_code": error.getErrorCode(), "detail": error.getErrorDescription()}


class InputEvent:
    """
    Class for storing input data

    Attributes:
        id (UUID4): id of event. Auto generating id.
        tags (list of str): the input image tag list.
        source (str): the event source.
        user_data (str): the created person user_data.
        img (bytearray): the input image.
        warped_img (int): flag shows if the input image is warped.
        external_id (str): the external_id for grouping.
        error (dict): an error which has been occurred while processing the event.
        create_time (timetamp): event create time.
        handler_id (UUID4): the handler id to process the event.
   """
    def __init__(self, img, source = None):
        self.id = str(uuid.uuid4())
        self.error = None
        self.create_time = getNowTimestampMillis()
        self.handler_id = None
        self.source = source
        self.img = img
        self.warped_img = 0
        self.external_id = None
        self.user_data = None
        self.tags = []

    @gen.coroutine
    def save(self):
        """
        Save the img to storage
        """
        path = getPath(self.id)
        if not os.path.exists(path):
            os.makedirs(path)
        eventImgFileName = "{}/{}.jpg".format(path, self.id)
        with open(eventImgFileName, 'wb') as f:
            f.write(self.img)

    def generateEvent(self) -> Event:
        """
        Generate an Event from the InputEvent object.

        :rtype: Event
        :return: an Event with the fulfilled fields
        """
        event = Event()
        for member in self.__dict__:
            if member in event.__dict__:
                event.__dict__[member] = self.__dict__[member]
        event.id = None
        return event
