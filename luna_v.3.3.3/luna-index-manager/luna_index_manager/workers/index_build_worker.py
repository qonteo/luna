"""
Module realize a worker for setting and monitoring tasks to indexer.
"""
from typing import Generator

from luna3.common.exceptions import LunaApiException
from luna3.core.core import CoreAPI
from tornado import gen
from tornado.ioloop import IOLoop

from configs.config import LUNA_CORE_ORIGIN, LUNA_CORE_API_VERSION, CONNECT_TIMEOUT, REQUEST_TIMEOUT
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.utils.log import Logger
from crutches_on_wheels.utils.rid import generateRequestId
from list_buffer.crawler import Crawler
from workers.index_upload_worker import UploadWorker
from workers.task import IndexTask
from workers.worker_queues import ReloadQueue


class IndexWorker:
    """
    Worker for building index in indexer.

    Worker monitors the buffer of global crawler. If the buffer is not empty the worker will pop a luna list from
    the buffer. After that the worker creates IndexTask and make "start create index" request to indexer with the list.
    It is monitors the index build. worker moves task to upload index  worker next step.

    Attributes:
        logger (Logger): logger
        currentTask (IndexTask): current task
        coreClient (CoreAPI): core client are creating for every task
        crawler (Crawler): crawler with the buffer
        reloadIndexesQueue (ReloadQueue): queue for reload index task
    """

    def __init__(self, crawler: Crawler, reloadIndexesQueue: ReloadQueue):
        self.logger = Logger()
        self.currentTask = None
        self.coreClient = CoreAPI(origin=LUNA_CORE_ORIGIN, api=LUNA_CORE_API_VERSION, asyncRequest=True,
                                  connectTimeout=CONNECT_TIMEOUT, requestTimeout=REQUEST_TIMEOUT)
        self.crawler = crawler
        self.reloadIndexesQueue = reloadIndexesQueue

    def updateClient(self, requestId: str) -> None:
        """
        Create new core client with new request id.
        Args:
            requestId: request id for task
        """
        self.coreClient = CoreAPI(origin=LUNA_CORE_ORIGIN, api=LUNA_CORE_API_VERSION, asyncRequest=True,
                                  lunaRequestId=requestId, connectTimeout=CONNECT_TIMEOUT,
                                  requestTimeout=REQUEST_TIMEOUT)

    @gen.coroutine
    def createIndexLoop(self) -> Generator[None, None, None]:
        """
        Infinity loop.

        Worker tries to get luna list from the crawler buffer.  If list is not None worker runs build index in the indexer
        and monitors it.
        """
        while True:
            try:
                lunaList = self.crawler.buffer.pop()
                if lunaList is None:
                    yield gen.sleep(1)
                    continue

                requestId = generateRequestId()
                self.logger = Logger(requestId)
                self.updateClient(requestId)

                self.currentTask = IndexTask(lunaList.listId, self.logger, requestId)
            except LunaApiException as e:
                self.logger.error(e.json)
                continue
            except Exception as e:
                self.logger.exception()
                continue

            try:
                self.logger.info("Start index list: {}, task: {}".format(lunaList.listId, self.currentTask.id))

                response = yield self.coreClient.startIndex(descriptorLists=[self.currentTask.listId], raiseError=False,
                                                            archive=True)
                if not response.success:
                    self.logger.info(
                        "Failed set task to index list: {}\n, reason: {}".format(lunaList.listId, response.json))
                    self.currentTask.fail(str(response.json))
                    continue
                self.logger.debug(response.json)
                self.currentTask.startIndex(response.json["generation"])
                yield self.waitBuildIndex()
                uploadWorker = UploadWorker(self.currentTask, self.reloadIndexesQueue)
                IOLoop.current().add_callback(uploadWorker.uploadIndex)

            except LunaApiException as e:
                self.currentTask.fail(str(e.json))
                self.logger.error(e.json)
            except VLException as e:
                self.currentTask.fail(e.error.detail)
                self.logger.error(e.error.detail)
            except Exception as e:
                self.logger.exception()
                self.currentTask.fail("Uncaught exception in index worker")
            finally:
                self.currentTask.finishIndex()

    @gen.coroutine
    def waitBuildIndex(self) -> Generator[None, None, None]:
        """
        Wait end of building index.

        Raises:
            VLException(Error.GenerationNotFound): if generation not found indexer after build index
            VLException(Error.UnknownStatusOfIndexer): if status of indexer is not 'build_index' or 'stopped'
        """
        while True:
            self.logger.debug("Wait index {}".format(self.currentTask.generation))
            response = yield self.coreClient.getStatus(raiseError=True)
            if response.json["status"] == 'build_index':
                yield gen.sleep(1)
                continue
            elif response.json["status"] == 'stopped':
                generations = (yield self.coreClient.getListGenerations(raiseError=True)).json["result"]
                generationNames = [generation["generation"] for generation in generations]
                if self.currentTask.generation in generationNames:
                    return
                raise VLException(Error.GenerationNotFound)
            else:
                self.logger.error(response.json)
                raise VLException(Error.UnknownStatusOfIndexer)
