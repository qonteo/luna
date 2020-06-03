from tornado import web, escape
import ujson as json
from jsonschema import validate, ValidationError
from tornado import gen
from analytics.common_objects import logger
from functools import wraps
from errors.error import Error


class BaseHandler(web.RequestHandler):

    def error(self,  status_code: int, error_code: int, message):
        """
        Finish the request with the provided error.

        :param status_code: status code to set
        :param error_code: the error code
        :param message: the error message
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
        Finish the request successfully.

        :param status_code: status code to set
        :param reply: reply object
        :return: None
        """
        self.set_header('Content-Type', 'application/json')
        self.set_status(status_code)
        self.finish(json.dumps(reply, ensure_ascii = False))

    def loads(self):
        """
        Get a json object from the request body.

        :return: None or json object
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
        JsonSchema validator.

        :param inputJson: json to validate
        :param schema: schema to validate by
        :return: True or False
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

    def options(self, *args, **kwargs):
        """
        OPTIONS default handler.

        :param args: function args
        :param kwargs: function kwargs
        :return: None
        """
        self.set_status(200)
        self.finish()

    def setMethodNotAllowed(self):
        """
        Default method not allowed handler.

        :return: None
        """
        self.set_status(405)
        self.write({'error_code': Error.MethodNotAllowed.getErrorCode(),
                    'detail': Error.MethodNotAllowed.getErrorDescription()})
        self.set_header('Content-Type', 'application/json')
        self.finish()

    def post(self, *args, **kwargs):
        """
        POST default handler.

        :param args: function args
        :param kwargs: function kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def put(self, *args, **kwargs):
        """
        PUT default handler.

        :param args: function args
        :param kwargs: function kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def patch(self, *args, **kwargs):
        """
        PATCH default handler.

        :param args: function args
        :param kwargs: function kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def delete(self, *args, **kwargs):
        """
        DELETE default handler.

        :param args: function args
        :param kwargs: function kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def head(self, *args, **kwargs):
        """
        HEAD default handler.

        :param args: function args
        :param kwargs: function kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def get(self, *args, **kwargs):
        """
        GET default handler.

        :param args: function args
        :param kwargs: function kwargs
        :return: None
        """
        self.setMethodNotAllowed()

    def data_received(self, chunk):
        pass


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
