"""
Module realize base handler
"""
from functools import wraps
from typing import Callable, Union, Any, Tuple, Optional

import ujson as json

import chardet
from luna3.common.exceptions import LunaApiException
from tornado import web, gen
from jsonschema import validate, ValidationError, SchemaError

from ..errors.errors import Error, ErrorInfo
from ..errors.exception import VLException
from ..utils.functions import isCoroutineFunction
from ..utils.log import Logger
from ..utils.rid import checkRequestId, generateRequestId


class VLBaseHandler(web.RequestHandler):
    """
    VL Base handler class.
    Attributes:
        logger(Logger): logger for request
        requestId(str): request id
    """

    def setMethodNotAllowed(self) -> None:
        """
        Set error "method not allowed" and status code 405
        """
        self.error(405, error=Error.MethodNotAllowed)

    def post(self, *args, **kwargs) -> None:
        """
        Method "POST", stub.
        """
        self.setMethodNotAllowed()

    def put(self, *args, **kwargs) -> None:
        """
        Method "PUT", stub.
        """
        self.setMethodNotAllowed()

    def patch(self, *args, **kwargs) -> None:
        """
        Method "PATCH", stub.
        """
        self.setMethodNotAllowed()

    def delete(self, *args, **kwargs) -> None:
        """
        Method "DELETE", stub.
        """
        self.setMethodNotAllowed()

    def head(self, *args, **kwargs) -> None:
        """
        Method "HEAD", stub.
        """
        self.setMethodNotAllowed()

    def get(self, *args, **kwargs) -> None:
        """
        Method "GET", stub.
        """
        self.setMethodNotAllowed()

    def options(self, *args, **kwargs) -> None:
        """
        Method "OPTIONS", stub.
        """
        self.setMethodNotAllowed()

    def data_received(self, chunk: bytes) -> None:
        """
        Stub for tornado function.

        Args:
            chunk: input bytes
        """
        pass

    def initialize(self):
        """
        Initialize logger for request and  create request id  and logger.

        RequestId consists of two parts. first - timestamp of server time or utc, second - uuid4.
        """
        self.requestId = self.request.headers.get("LUNA-Request-Id", "")
        if not (checkRequestId(self.requestId)):
            self.requestId = generateRequestId()

        self.logger = Logger(self.requestId)
        self.logger.info("Uri: {}".format(self.request.uri))

    def getQueryParam(self, name: str, validator: Callable = lambda x: x, require: bool = False,
                      default: Any = None) -> Any:
        """
        Getting query param

        Args:
            name: name of param
            validator: param validator and converter from str to correct format
            require: whether param is required
            default: default value of param
        Returns:
            value
        Raises:
            VLException(Error.QueryParameterNotFound, 400): if require param not found
            VLException(Error.BadQueryParams, 400): if format of param is incorrect
        """
        valueStr = self.get_query_argument(name, None)
        if valueStr is None:
            if not require:
                return default
            else:
                error = Error.formatError(Error.QueryParameterNotFound, name)
                raise VLException(error, 400, False)
        try:
            return validator(valueStr)
        except ValueError:

            error = Error.formatError(Error.BadQueryParams, name)
            raise VLException(error, 400, False)

    def getPagination(self, defaultPage: int = 1, defaultPageSize: int = 10, maxPageSize: int = 100) -> Tuple[int, int]:
        """
        Getting pagination

        Args:
            maxPageSize: max elements by page
            defaultPage: default page
            defaultPageSize: default page size
            pair page and page_size
        Returns:
            pair page and page size
        """
        page = self.getQueryParam("page", lambda params: max(int(params), 1), default=defaultPage)
        pageSize = self.getQueryParam("page_size", lambda params: max(min(int(params), maxPageSize), 1),
                                      default=defaultPageSize)
        return page, pageSize

    def finish(self, *args, **kwargs):
        """
        Function is adding "LUNA-Request-Id" to response.

        Args:
            args: params
        Keyword Args:
            kwargs
        """
        self.set_header("LUNA-Request-Id", self.requestId)
        super().finish(*args, **kwargs)

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
        responseJson = {'error_code': error.errorCode, 'detail': error.detail, "desc": error.description}
        self.finish(json.dumps(responseJson, ensure_ascii=False))

    def success(self, statusCode: int = 200, body: Optional[Union[float, int, bytes, str]] = None,
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
        self.set_status(statusCode)
        if outputJson is not None:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(outputJson, ensure_ascii=False))

        elif body is not None:
            self.set_header("Content-Type", contentType)
            self.write(body)

        self.set_header("LUNA-Request-Id", self.requestId)
        self.finish()

    def getInputText(self) -> str:
        """
        Convert body to string.

        Encoding will be guessed using ``chardet``.

        Returns:
            decode body
        """
        if self.request.body is None:
            return ""
        encoding = chardet.detect(self.request.body)['encoding']
        # Decode unicode from given encoding.
        try:
            content = str(self.request.body, encoding, errors='replace')
        except (LookupError, TypeError):
            # A LookupError is raised if the encoding was not found which could
            # indicate a misspelling or similar mistake.
            #
            # A TypeError can be raised if encoding is None
            #
            # So we try blindly encoding.
            content = str(self.request.body, errors='replace')
        return content

    def getInputJson(self) -> Union[dict, list, int, float]:
        """
        Load  body from request to json

        Returns:
            json
        Raises:
            VLException(Error.RequestNotContainsJson, 400): if failed  to load json
        """
        try:
            text = self.getInputText()
            return json.loads(text)
        except ValueError:
            raise VLException(Error.RequestNotContainsJson, 400, isCriticalError=False)

    @staticmethod
    def validateJson(data: Union[int, dict, list], schema: dict) -> None:
        """
        Validate json.

        Args:
            data: json for validation
            schema: json schema
        Raises:
            VLException(Error.BadInputJson, 400): if failed  to validate schema
        """
        try:
            validate(data, schema)
        except (ValidationError, SchemaError) as e:
            path = ""
            for count, p in enumerate(e.path):
                path += str(p)
                if count != len(e.path) - 1:
                    path += "."

            error = Error.formatError(Error.BadInputJson, path, e.message)
            raise VLException(error, 400, isCriticalError=False)

    @staticmethod
    def createErrorFromLunaApiException(exception: LunaApiException) -> ErrorInfo:
        """
        Generate from LunaApiException a ErrorInfo
        Args:
            exception: exception from luna3

        Returns:
            ErrorInfo
        """
        if "error" in exception.json:
            error = ErrorInfo(exception.json["error"], exception.json["desc"], exception.json["detail"])
        else:
            error = ErrorInfo(exception.json["error_code"], exception.json["desc"], exception.json["detail"])
        return error

    @staticmethod
    def requestExceptionWrap(func: Callable) -> Callable:
        """
        Decorator for catching exceptions in processing request request.

        If exception was caught, system calls error method with error code RequestInternalServerError.

        Args:
            func: decorated function
        Returns:
            wrapped function
        """

        if isCoroutineFunction(func):
            @wraps(func)
            @gen.coroutine
            def wrap(*func_args, **func_kwargs):
                try:
                    yield func(*func_args, **func_kwargs)
                except VLException as e:
                    if e.isCriticalError:
                        func_args[0].logger.exception()
                    return func_args[0].error(e.statusCode, error=e.error)
                except LunaApiException as e:
                    error = VLBaseHandler.createErrorFromLunaApiException(e)
                    return func_args[0].error(e.statusCode, error=error)
                except Exception as e:
                    func_args[0].logger.exception()
                    return func_args[0].error(500, Error.RequestInternalServerError)
        else:
            @wraps(func)
            def wrap(*func_args, **func_kwargs):
                try:
                    func(*func_args, **func_kwargs)
                except VLException as e:
                    if e.isCriticalError:
                        func_args[0].logger.exception()
                    return func_args[0].error(e.statusCode, error=e.error)
                except LunaApiException as e:
                    error = VLBaseHandler.createErrorFromLunaApiException(e)
                    return func_args[0].error(e.statusCode, error=error)
                except Exception as e:
                    func_args[0].logger.exception()
                    return func_args[0].error(500, Error.RequestInternalServerError)

        return wrap
