"""
Module realize VLException, exception for internal usages
"""
from .errors import ErrorInfo


class VLException(Exception):
    """
    VLException

    Attributes:
        error: error
        statusCode: status code for response
        isCriticalError: print trace or not
    """

    def __init__(self, error: ErrorInfo, statusCode=500, isCriticalError=True, exception=None):
        super(VLException, self).__init__(error.description)
        self.error = error
        self.statusCode = statusCode
        self.isCriticalError = isCriticalError
        self.exception = exception
