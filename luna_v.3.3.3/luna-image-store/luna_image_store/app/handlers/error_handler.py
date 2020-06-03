from app.handlers.base_handler import BaseRequestHandler
from crutches_on_wheels.handlers.error_getters import get404Error


class ErrorHandler404(BaseRequestHandler):
    """
    Error handler for  incorrect  request resources
    """

    def prepare(self):
        """
        Finish request and  set error Error.PageNotFoundError
        """
        error = get404Error(self.request)
        self.error(404, error)
