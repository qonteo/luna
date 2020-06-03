from functools import lru_cache

from tornado import web, gen

from app.common_objects import timer, LUNA_CLIENT
from app.handlers.base_handler import BaseHandler, coRequestExeptionWrap
from version import VERSION


class VersionHandler(BaseHandler):
    """
    Version handler.
    """
    @web.asynchronous
    @timer.timerTor
    @coRequestExeptionWrap
    @gen.coroutine
    def get(self):
        """
        Get version handler.
        :return: None
        """
        lunaAPIVersion = LUNA_CLIENT.getVersion(raiseError=True).body
        full_version = {"facestreammanager2": VERSION['Version'], **lunaAPIVersion['Version']}
        self.success(200, full_version)
