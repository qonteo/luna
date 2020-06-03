from app.handlers.base_handler import BaseHandler
from crutches_on_wheels.errors.errors import Error


class ErrorHandler404(BaseHandler):
    """
    Error handler for incorrect request resources
    """

    def prepare(self) -> None:
        """
        Finish request and set error Error.PageNotFoundError
        """
        self.error(404, error=Error.PageNotFoundError)
