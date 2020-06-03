from errors.error import Error
from app.handlers.base_handler import BaseHandler


class ErrorHandler404(BaseHandler):
    """
    Base 404 handler.
    """
    def prepare(self):
        return self.error(404, Error.PageNotFoundError.getErrorCode(),
                          Error.PageNotFoundError.getErrorDescription())
