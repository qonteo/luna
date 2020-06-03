"""
Module realize luna-list crawler

Attributes:
    facesClient: client for luna-faces.
"""
from luna3.common.exceptions import LunaApiException
from luna3.faces.faces import FacesApi
from tornado import gen, ioloop
from typing import Generator, List

from configs.config import LUNA_FACES_ORIGIN, LUNA_FACES_API_VERSION, \
    MIN_FACES_IN_LIST_FOR_INDEXING, INDEXED_FACES_LISTS, CONNECT_TIMEOUT, REQUEST_TIMEOUT
from crutches_on_wheels.utils.log import Logger
from crutches_on_wheels.utils.rid import generateRequestId
from crutches_on_wheels.utils.timer import timer
from list_buffer.buffer import ListBuffer, LunaList
from db.context import DBContext
from utils.functions import convertToDateTime


facesClient = FacesApi(LUNA_FACES_ORIGIN, LUNA_FACES_API_VERSION, asyncRequest=True,
                       connectTimeout=CONNECT_TIMEOUT, requestTimeout=REQUEST_TIMEOUT)


class Crawler:
    """
    Crawler assemble lists from luna-faces and put it to buffer for indexing (if need).

    Attributes:
        period: periodicity of getting lists data from luna-faces (in minutes)
        buffer (ListBuffer): queue for waiting indexation
        taskId (str): str as request id for request to luna-faces.
    """

    def __init__(self, period: int):
        self.period = period
        self.buffer = ListBuffer()
        self.logger = Logger()
        self.requestId = None
        self.dbContext = DBContext(self.logger)

    def updateLogger(self):
        self.logger = Logger(self.requestId)
        self.dbContext = DBContext(self.logger)

    @gen.coroutine
    def checkIndexationCriterion(self, listId):
        response = (yield facesClient.getList(listId, raiseError=True, lunaRequestId=self.requestId,
                                              pageSize=0)).json
        lunaList = LunaList(response["list_id"], response["last_update_time"], response["face_count"])
        if INDEXED_FACES_LISTS == ["all"]:
            if lunaList.faceCount < MIN_FACES_IN_LIST_FOR_INDEXING:
                return False, lunaList
        else:
            if lunaList.listId not in INDEXED_FACES_LISTS:
                return False, lunaList
        return True, lunaList

    @timer
    @gen.coroutine
    def getListsForIndexing(self) -> Generator[None, None, List[LunaList]]:
        """
        Get lists from luna-faces for indexing.

        Returns:
            all lists which have face count greater than MIN_FACES_IN_LIST_FOR_INDEXING.
        """
        def isListNeedToIndex(lunaList: dict) -> bool:
            """
            Check that luna list is already indexed

            Args:
                lunaList: luna list
            Returns:
                true if list need to index
            """
            startIndexTime = self.dbContext.getSuccessStartIndexTimeOfList(lunaList['list_id'])
            if startIndexTime is not None:
                if (convertToDateTime(lunaList['last_update_time'])) <= startIndexTime:
                    return False
            if self.dbContext.isTaskForListInProgress(lunaList['list_id']):
                return False
            return True

        lists = []
        if INDEXED_FACES_LISTS == ["all"]:
            listCount = (yield facesClient.getLists(raiseError=True)).json["count"]
            pageSize = 100
            pageCount = (listCount + pageSize - 1) // pageSize
            for page in range(pageCount + 1):
                facesLists = (yield facesClient.getLists(page=page, pageSize=pageSize, raiseError=True,
                                                         lunaRequestId=self.requestId)).json["lists"]
                lists.extend(
                    [faceList for faceList in facesLists if faceList["face_count"] >= MIN_FACES_IN_LIST_FOR_INDEXING])
        else:
            for lunaList in INDEXED_FACES_LISTS:
                facesList = (yield facesClient.getList(listId=lunaList, pageSize=0, raiseError=True,
                                                       lunaRequestId=self.requestId)).json
                lists.append(facesList)
        return [LunaList(lunaList["list_id"], lunaList["last_update_time"], lunaList["face_count"]) for lunaList in
                lists if isListNeedToIndex(lunaList)]

    @timer
    @gen.coroutine
    def assembleLists(self) -> Generator[None, None, None]:
        """
        Get lists from luna faces and put them to the buffer.
        """
        self.requestId = generateRequestId()
        self.updateLogger()
        self.logger.info("Start crawling")
        try:
            lists = yield self.getListsForIndexing()
        except LunaApiException as e:
            self.logger.error(e.json)
            self.logger.error("End of crawling, api error")
            return
        except ConnectionError:
            self.logger.exception()
            self.logger.error("End of crawling, connection error")
            return
        self.buffer.extend(lists)
        self.logger.info(("End of crawling, buffer size:  {}".format(len(self.buffer.listsForIndexing))))

    def startCrawling(self) -> None:
        """
        Start crawling.
        """
        callback = ioloop.PeriodicCallback(self.assembleLists, int(1000 * 60 * self.period))
        callback.start()
