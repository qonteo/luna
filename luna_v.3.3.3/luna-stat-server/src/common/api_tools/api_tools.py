from abc import abstractmethod

from .utils import partially_format


class ApiError(ValueError):
    """
    Exception class to hold and send as response
    """
    code = 400
    description = 'Abstract error'

    def __init__(self, **fields):
        self.fields = fields

    def describe(self):
        return partially_format(self.description, **self.fields)

    def as_response(self):
        return {
            'code': self.code,
            'text': self.describe()
        }


class RedisError(ApiError):
    code = 400
    description = '2001: {description}'


class InfluxError(ApiError):
    code = 400
    description = '2002: {description}'


class NotValidJson(ApiError):
    code = 400
    description = '1001: Cannot parse json {json}'


class BadRequest(ApiError):
    code = 400
    description = '400: Bad Request {description}'


class NotFoundError(ApiError):
    code = 404
    description = 'Resource "[{method}] {path}" not found'

    def describe(self):
        if self.description is NotFoundError.description:
            if 'path' not in self.fields and 'method' not in self.fields:
                return 'Resource not found'

        return super().describe()


class InternalError(ApiError):
    code = 500
    description = 'Internal error'


class ClassHandler(object):
    WRAP_API_ERROR = True
    LOG = None

    @abstractmethod
    def initialize(self, **kwargs):
        pass

    @classmethod
    def create_handlers(cls, deps):
        instance = cls()
        instance.initialize(**deps)
        return {
            m.upper(): getattr(instance, m)
            for m in ('get', 'head', 'post', 'delete', 'patch', 'put', 'options')
            if hasattr(instance, m)
        }
