"""
Module contains global workers and queue
Attributes
    crawler (Crawler): crawler for assemble lists from luna-faces
"""
from configs.config import CRAWLER_PERIOD
from list_buffer.crawler import Crawler
from workers.index_build_worker import IndexWorker
from workers.worker_queues import ReloadQueue

crawler = Crawler(CRAWLER_PERIOD)
reloadIndexQueue = ReloadQueue()
indexWorker = IndexWorker(crawler, reloadIndexQueue)