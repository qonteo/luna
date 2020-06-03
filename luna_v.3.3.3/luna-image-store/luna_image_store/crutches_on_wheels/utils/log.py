"""Loggers

Loggers module.
"""
import logbook
import sys
from logbook import StreamHandler
from logbook import Logger as BaseLogger
from typing import Optional
import time

from os import path

StreamHandler(sys.stdout).push_application()


class Logger(BaseLogger):
    """
    Application logger
    """
    LOG_LEVEL = logbook.DEBUG
    LOG_TIME = "LOCAL"

    APP_NAME = ""
    LOGS_FILE_HANDLERS = []

    @staticmethod
    def getLogLevel(log_level) -> int:
        """
        Get log level from config for logger.

        Returns:
            int: if LOG_LEVEL not set or incorrect will return logbook.NOTSET
        """
        if log_level == "DEBUG":
            return logbook.DEBUG
        if log_level == "ERROR":
            return logbook.ERROR
        if log_level == "INFO":
            return logbook.INFO
        if log_level == "WARNING":
            return logbook.WARNING
        return logbook.NOTSET

    @classmethod
    def initiate(cls, appName: str = "", logLevel: str = "DEBUG", logTime: str = "LOCAL",
                 folderForLog: str = "./") -> None:
        """
        Initiate class settings.

        Args:
            appName: application name
            logLevel: log level
            logTime: time of logs
            folderForLog: folder with log-files

        """
        cls.LOG_LEVEL = cls.getLogLevel(logLevel)
        cls.LOG_TIME = logTime
        cls.APP_NAME = appName
        DEBUG_FILE_HANDLER = logbook.FileHandler(path.join(folderForLog, "{}_DEBUG.txt".format(appName)),
                                                 level='DEBUG', bubble=True)

        ERROR_FILE_HANDLER = logbook.FileHandler(path.join(folderForLog, "{}_ERROR.txt".format(appName)),
                                                 level='ERROR', bubble=True)
        cls.LOGS_FILE_HANDLERS = [DEBUG_FILE_HANDLER, ERROR_FILE_HANDLER]

        if cls.LOG_TIME == "LOCAL":
            for handler in cls.LOGS_FILE_HANDLERS:
                handler.formatter.converter = time.localtime
            logbook.set_datetime_format("local")

    def __init__(self, template: Optional[str] = None) -> None:
        """
        Init logger.

        Args:
            template: string for marking logs. Typical usage - request id.
        """
        templateString = '{} {}'.format(Logger.APP_NAME, template) if template is not None else Logger.APP_NAME
        super().__init__(templateString)
        self.level = Logger.LOG_LEVEL
        self.handlers.extend(Logger.LOGS_FILE_HANDLERS)
