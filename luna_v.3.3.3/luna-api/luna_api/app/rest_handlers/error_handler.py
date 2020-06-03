from app.rest_handlers.base_handler_class import BaseRequestHandler
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.handlers.error_getters import get404Error


class ErrorHandler404(BaseRequestHandler):
    def prepare(self):
        error = Error.generateError(get404Error(self.request), "Page not found")
        self.error(404, error)
