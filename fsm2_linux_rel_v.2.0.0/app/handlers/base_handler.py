from tornado import web, escape
import ujson as json
from jsonschema import validate, ValidationError
from tornado import gen
from app.common_objects import logger
from functools import wraps
from errors.error import Error


class BaseHandler(web.RequestHandler):

    def error(self,  status_code: int, error_code: int, message):
        """
        Finish the request with an error.

        :param status_code: the response status code
        :param error_code: the error code in json response
        :param message: the error message in json response
        :return: None
        """
        msg = "uri: {}".format(self.request.uri) + "\n"
        msg += "request failed, reason: {}".format(str(error_code)) + "\n"
        msg += "status code: {}".format(status_code)

        logger.debug(msg)
        self.set_header('Content-Type', 'application/json')
        self.set_status(status_code)
        responseJson = {'error_code': error_code, 'detail': message}
        self.finish(json.dumps(responseJson, ensure_ascii = False))

    def success(self, status_code, reply):
        """
        Finish the request with success response.

        :param status_code: the response status code
        :param reply: the reply json as dict
        :return: None
        """
        self.set_header('Content-Type', 'application/json')
        self.set_status(status_code)
        self.finish(json.dumps(reply, ensure_ascii = False))

    def loads(self):
        """
        The request json loads. Finish the request with the error if an error occurred.

        :return: loaded json or None if an error occurred
        """
        body = self.request.body
        try:
            return escape.json_decode(body)
        except ValueError:
            self.error(400, Error.RequestNotContainsJson.getErrorCode(),
                       Error.RequestNotContainsJson.getErrorDescription())
            return None
        except Exception as e:
            logger.debug(e)
            self.error(400, Error.RequestNotContainsJson.getErrorCode(),
                       Error.RequestNotContainsJson.getErrorDescription())
            return None

    def validateJson(self, inputJson, schema):
        """
        Jsonschema validator.

        :param inputJson: a json to validate
        :param schema: a schema to validate with
        :return: True if succeed, False if failed finish request also
        """
        try:
            validate(inputJson, schema)
            return True
        except ValidationError as e:
            logger.debug(e)
            path = ""
            for count, p in enumerate(e.path):
                path += str(p)
                if count != len(e.path) - 1:
                    path += "."
            error = Error.generateError(Error.BadInputJson, "Failed to validate input json. Path: '{}',  message: '{}'"
                                                            "".format(path, e.message))
            self.error(400, error.getErrorCode(), error.getErrorDescription())
            return False

    def validateQueries(self, inputQueries, schema):
        """
        Query parameters validator.

        :param inputQueries: a json to validate
        :param schema: a schema to validate with
        :return: True if succeed, False if failed finish request also
        """
        try:
            validate(inputQueries, schema)
            return True
        except ValidationError as e:
            logger.debug(e)
            self.error(400, Error.BadQueryParam.getErrorCode(), Error.BadQueryParam.getErrorDescription().format(e.args[0]))
            return False

    def options(self, *args, **kwargs):
        """
        OPTIONS method handler.

        :param args: request handler args
        :param kwargs: request handler kwargs
        :return: None
        """
        self.set_status(200)
        self.finish()

    def setMethodNotAllowed(self):
        """
        Set method not allowed for known request methods.

        :return: None
        """
        self.set_status(405)
        self.write({'error_code': Error.MethodNotAllowed.getErrorCode(),
                    'detail': Error.MethodNotAllowed.getErrorDescription()})
        self.set_header('Content-Type', 'application/json')
        self.finish()

    def post(self, *args, **kwargs):
        """
        POST request method default handler.

        :param args: request handler args
        :param kwargs: request handler kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def put(self, *args, **kwargs):
        """
        PUT request method default handler.

        :param args: request handler args
        :param kwargs: request handler kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def patch(self, *args, **kwargs):
        """
        PATCH request method default handler.

        :param args: request handler args
        :param kwargs: request handler kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def delete(self, *args, **kwargs):
        """
        DELETE request method default handler.

        :param args: request handler args
        :param kwargs: request handler kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def head(self, *args, **kwargs):
        """
        HEAD request method default handler.

        :param args: request handler args
        :param kwargs: request handler kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def get(self, *args, **kwargs):
        """
        GET request method default handler.

        :param args: request handler args
        :param kwargs: request handler kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def data_received(self, chunk):
        """
        Streamed request data handle.

        :param chunk: stream data chunk
        :return: None
        """
        pass

    def set_default_headers(self):
        """
        Set default response headers.

        :return: None
        """
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Credentials", 'true')
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Auth-Token")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, OPTIONS, PATCH, DELETE')


def coRequestExeptionWrap(func):
    """
    Decorator for catching exceptions in asynchronous request.

    :param func: decorated function
    :return: if exception was caught, system calls error method with error code RequestInternalServerError.
    """
    @wraps(func)
    @gen.coroutine
    def wrap(*func_args, **func_kwargs):
        try:
            yield func(*func_args, **func_kwargs)
        except Exception as e:
            logger.exception(e)
            return func_args[0].error(500, Error.RequestInternalServerError.getErrorCode(),
                                      Error.InternalServerError.getErrorDescription())

    return wrap


def requestExeptionWrap(func):
    """
    Decorator for catching exceptions in synchronous request.

    :param func: decorated function
    :return: if exception was caught, system calls error method with error code RequestInternalServerError.
    """

    @wraps(func)
    def wrap(*func_args, **func_kwargs):
        try:
            func(*func_args, **func_kwargs)
        except Exception as e:
            logger.exception(e)
            return func_args[0].error(500, Error.RequestInternalServerError.getErrorCode(),
                                      Error.InternalServerError.getErrorDescription())

    return wrap