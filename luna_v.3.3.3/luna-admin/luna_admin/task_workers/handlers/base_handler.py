import ujson as json
from crutches_on_wheels.handlers.base_handler_class import VLBaseHandler
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from functools import wraps
from tornado import gen


class BaseHandler(VLBaseHandler):

    def badAuth(self, errCode, msg):
        """
        Response to unsuccessful attempt to access resource, which requires authorization.

        Response contains header 'WWW-Authenticate' with description of authorization format.
        Response body contains json with error description.
        """
        self.set_header('Content-Type', 'application/json')
        self.set_header('WWW-Authenticate', 'Basic realm="login:password"')
        self.set_status(401)
        self.finish(json.dumps({'error_code': errCode,
                                'detail': msg}, ensure_ascii=False))

    @staticmethod
    def coRequestExceptionWrap(func):
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
            except VLException as e:
                if e.isCriticalError:
                    func_args[0].logger.exception()
                return func_args[0].error(e.statusCode, error=e.error)
            except Exception:
                func_args[0].logger.exception()
                return func_args[0].error(500, Error.RequestInternalServerError.errorCode,
                                          Error.InternalServerError.description)

        return wrap
