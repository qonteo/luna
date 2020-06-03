# -*- coding: utf-8 -*-
"""
Module for 404 error handler.
"""
from app.handlers.base_handler import BaseRequestHandler
from crutches_on_wheels.errors.errors import Error


class ErrorHandler404(BaseRequestHandler):
    """
    Error handler for  incorrect  request resources.
    """

    def prepare(self):
        """
        Finish request and  set error Error.PageNotFoundError
        """
        self.error(404, error=Error.PageNotFoundError)
