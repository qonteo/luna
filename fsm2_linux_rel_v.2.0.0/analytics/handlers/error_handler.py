from errors.error import Error
from analytics.handlers.base_handler import BaseHandler


class ErrorHandler404(BaseHandler):
    """
    Default 404 handler.
    """
    def prepare(self):
        return self.error(404, Error.PageNotFoundError.getErrorCode(),
                          Error.PageNotFoundError.getErrorDescription())
