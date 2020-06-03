"""
Module realize getters for errors.
"""
from tornado.httputil import HTTPServerRequest
from ..errors.errors import Error, ErrorInfo


def get404Error(request: HTTPServerRequest) -> ErrorInfo:
    """
    Args:
        request: input request
    Returns:
        formatted Error.PageNotFoundError
    """
    return Error.formatError(Error.PageNotFoundError, request.uri)
