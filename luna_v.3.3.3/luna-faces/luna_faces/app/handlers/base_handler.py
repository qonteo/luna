import time
import ujson as json
import uuid
import logbook
from configs.config import FOLDER_WITH_LOGS, STORAGE_TIME
from db.context import DBContext
from crutches_on_wheels.handlers.base_handler_class import VLBaseHandler
from crutches_on_wheels.errors.errors import Error, ErrorInfo
from crutches_on_wheels.utils.regexps import REQUEST_ID_REGEXP
from crutches_on_wheels.utils.log import Logger


FILE_HANDLERS = (
    logbook.FileHandler(FOLDER_WITH_LOGS + "./luna-faces_DEBUG.txt", level='DEBUG', bubble=True),
    logbook.FileHandler(FOLDER_WITH_LOGS + "/luna-faces_ERROR.txt", level='ERROR', bubble=True)
)

TIME_ZONE_DELTA = time.timezone  #: correction for getting timestamp in utc


class BaseRequestHandler(VLBaseHandler):
    """
    Base handler for other handlers.
    """

    def initialize(self):
        """
        Initialize logger for request and  create request id and contexts to Postgres and LunaCore.

        RequestId consists of two parts. first - timestamp of server time or utc, second - short id, first 8 symbols
        from uuid4.
        """
        super().initialize()
        self.set_header("Begin-Request-Time", str(time.time()))
        self.dbContext = DBContext(self.logger)

    def finish(self, *args, **kwargs):
        """
        Function is adding "LUNA-Request-Id" to response.

        Args:
            args: params
            kwargs: params
        """
        self.set_header("End-Request-Time", str(time.time()))
        super().finish(*args, **kwargs)
