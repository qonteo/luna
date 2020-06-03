import time
import ujson as json

from typing import Optional, Union

from app.common import luna3Client, generateLuna3Client
from app.tornado_request_function import LunaCoreContext
from configs.config import ACCESS_CONTROL_ALLOW_ORIGIN, LOG_TIME
from crutches_on_wheels.errors.errors import Error, ErrorInfo
from crutches_on_wheels.handlers.base_handler_class import VLBaseHandler
from crutches_on_wheels.utils import rid
from db.db_function import DBContext


class StatisticsData:
    """
    Structure, where statistics is saved. Saved fields:
     1) start time of the request;
     #) duration of the request;
     #) json from the response;
     #) flag, that indicates whether request was successful or not;
     #) authorization type.
    """

    def __init__(self):
        self.startTime = time.time()  #: Start time of the request
        self.requestTime = 0  #: Duration of the request
        self.responseJson = {}  #: json
        self.isSuccess = True  #: flag, that indicates whether request was successful or not
        self.auth = ""  #: authorization type


class BaseRequestHandler(VLBaseHandler):

    def set_default_headers(self)->None:
        """
        Set default headers. Now it is CORS headers.
        """
        self.set_header("Access-Control-Allow-Origin", ACCESS_CONTROL_ALLOW_ORIGIN)
        if ACCESS_CONTROL_ALLOW_ORIGIN != "*":
            self.set_header("Access-Control-Allow-Credentials", 'true')
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Auth-Token")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PATCH, DELETE')

    def setMethodNotAllowed(self):
        self.set_status(405)
        self.write({'error_code': Error.MethodNotAllowed.errorCode,
                    'detail': Error.MethodNotAllowed.description})
        self.set_header('Content-Type', 'application/json')
        self.finish()

    def options(self, *args, **kwargs)-> None:
        """
        Default method option. By default 200 without body.

        Args:
            *args: args
            **kwargs: kwargs
        """
        self.set_status(200)
        self.finish()

    def initialize(self) -> None:
        """
        Initialize logger for request and  create request id and contexts to Postgres and LunaCore.

        RequestId consists of two parts. first - timestamp of server time or utc, second - short id, first 8 symbols
        from uuid4.
        """
        super().initialize()
        self.dbContext = DBContext(self.logger)
        self.luna3Client = generateLuna3Client(self.requestId)
        self.lunaCoreContext = LunaCoreContext(self.logger, self.luna3Client)
        self.statistiData = StatisticsData()

    def setRequestResult(self, responseJson: dict, isSuccess: bool) -> None:
        """
        Installation of response result

        Args:
            responseJson: dict with response result
            isSuccess: flag, which indicates whether response was successful or not
        """
        self.statistiData.requestTime = time.time() - self.statistiData.startTime
        self.statistiData.isSuccess = isSuccess
        self.statistiData.responseJson = responseJson

    def error(self, status_code: int, error: ErrorInfo) -> None:
        """
        Function, that sends error response. Calls installation of request result.

        Args:
            status_code: response status code
            error:  error
        """

        msg = "uri: {}, method: {}\n".format(self.request.uri, self.request.method)
        msg += "  request failed, reason: {}\n".format(str(error.errorCode))
        msg += "  desc: {}\n".format(error.description)
        msg += "  detail: {}\n".format(error.detail)
        msg += "  status code: {}".format(status_code)

        self.logger.info(msg)
        self.set_header('Content-Type', 'application/json')
        self.set_status(status_code)
        responseJson = {'error_code': error.errorCode, 'detail': error.detail}
        self.setRequestResult(responseJson, False)
        self.finish(json.dumps(responseJson, ensure_ascii=False))

    def success(self, statusCode: int = 200, body: Optional[Union[float, int, bytes, str, dict]] = None,
                outputJson: Optional[Union[dict, list, bytes, str]] = None,
                contentType: Optional[str] = None) -> None:
        """
        Finish  success request. Generate correct reply with request id header, correct  Content type header

        Args:
            contentType: body content type
            statusCode: response status code, range(200, 300), default 200
            body: pure body
            outputJson: json as object
        """
        self.setRequestResult(outputJson, True)
        super().success(statusCode, body, outputJson, contentType)
