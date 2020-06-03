# -*- coding: utf-8 -*-
""" Base handler

Module realize base class for all handlers.
"""

from crutches_on_wheels.handlers.base_handler_class import VLBaseHandler
from db.context import DBContext


class BaseRequestHandler(VLBaseHandler):
    """
    Base handler for other handlers.

    Attributes:
        logger (Logger): logger for input request
        requestId (str): request id
    """

    def initialize(self):
        """
        Initialize logger for request and  create request id and contexts to Postgres and LunaCore.

        RequestId consists of two parts. first - timestamp of server time or utc, second - short id, first 8 symbols
        from uuid4.
        """
        super().initialize()
        self.dbContext = DBContext(self.logger)
