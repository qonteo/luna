# -*- coding: utf-8 -*-
"""Application server.

Module with routing settings and application server.

Attributes:

    API (int): application api version
    application (Application): application server
"""
from tornado import web
from tornado.web import StaticFileHandler
import os

from app.handlers.error_handler import ErrorHandler404
from app.handlers.indexed_lists_handler import IndexedListHandler
from app.handlers.indexes_handlers import IndexesHandler
from app.handlers.queue_handler import QueueHandler
from app.handlers.version_handler import VersionHandler
from app.version import VERSION
from configs.config import FOLDER_WITH_LOGS, LOG_TIME, LOG_LEVEL, APP_NAME
from crutches_on_wheels.utils.log import Logger

API = VERSION["Version"]["api"]


application = web.Application([(r"/version", VersionHandler),
                               (r"/{}/indexes".format(API), IndexesHandler),
                               (r"/{}/queue".format(API), QueueHandler),
                               (r"/{}/indexes/lists".format(API), IndexedListHandler),
                               (r'/view/(.*)', StaticFileHandler,
                               {'path': os.path.join(os.path.abspath(''), 'app', 'handlers', 'html')}),
                               ],
                              default_handler_class=ErrorHandler404, )

Logger.initiate(APP_NAME, LOG_LEVEL, LOG_TIME, FOLDER_WITH_LOGS)
logger = Logger()  # : logger for debug printing, in standard mode
