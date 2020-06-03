from tornado import web
from app.common_objects import logger
import ujson as json
from tornado import gen
from tornado import httpclient
from tornado.httpclient import HTTPRequest
from configs.config import LUNA_API_TOKEN, LUNA_API_PORT, LUNA_API_API_VERSION, LUNA_API_HOST, CONNECT_TIMEOUT, \
    REQUEST_TIMEOUT
from errors.error import Result, Error


def generateLunaTornadoRequestError(reply):
    """
    Generate error from q bad Luna API reply.

    :param reply: a bad Luna API reply
    :return: result:
        Fail with corresponding error
    """
    if reply.request_time >= CONNECT_TIMEOUT or reply.request_time >= REQUEST_TIMEOUT:
        if reply.error.message == 'Timeout while connecting':
            logger.error(Error.LunaConnectionTimeout.getErrorDescription())
            return Result(Error.LunaConnectionTimeout, reply.error.message)
        else:
            logger.error(Error.LunaRequestTimeout.getErrorDescription())
            return Result(Error.LunaRequestTimeout, reply.error.message)
    if reply.error.__class__.__name__ == 'ConnectionRefusedError':
        logger.error(Error.LunaRequestError.getErrorDescription())
        error = Error.generateError(Error.LunaRequestError,
                                    Error.LunaRequestError.getErrorDescription().format("Proxy", reply.code,
                                                                                        'connection refused'))
        return Result(error, error.getErrorDescription())
    if hasattr(reply.error, "errno"):
        error = Error.generateError(Error.LunaRequestError,
                                    Error.LunaRequestError.getErrorDescription().format("Proxy", reply.code,
                                                                                        reply.error.errno))
        logger.error(reply.error.errno)
        return Result(error, error.getErrorDescription())
    if hasattr(reply.error, "message"):
        error = Error.generateError(Error.LunaRequestError,
                                    Error.LunaRequestError.getErrorDescription().format("Proxy", reply.code,
                                                                                        reply.error.message))
        logger.error(reply.error.message)
        return Result(error, error.getErrorDescription())

    error = Error.generateError(Error.LunaRequestError,
                                Error.LunaRequestError.getErrorDescription().format("Proxy", reply.code,
                                                                                    "unknown error"))
    logger.error("unknown error")
    return Result(error, error.getErrorDescription())


class LunaProxyHandler(web.RequestHandler):
    """
    Luna API proxy handler.
    """
    @web.asynchronous
    @gen.coroutine
    def post(self, *args, **kwargs):
        """
        POST Luna API proxy request handler.

        :param args: request args
        :param kwargs: request kwargs
        :return: None
        """
        yield self.proxyRequest()

    @web.asynchronous
    @gen.coroutine
    def put(self, *args, **kwargs):
        """
        PUT Luna API proxy request handler.

        :param args: request args
        :param kwargs: request kwargs
        :return: None
        """
        yield self.proxyRequest()

    @web.asynchronous
    @gen.coroutine
    def patch(self, *args, **kwargs):
        """
        PATCH Luna API proxy request handler.

        :param args: request args
        :param kwargs: request kwargs
        :return: None
        """
        yield self.proxyRequest()

    @web.asynchronous
    @gen.coroutine
    def delete(self, *args, **kwargs):
        """
        DELETE Luna API proxy request handler.

        :param args: request args
        :param kwargs: request kwargs
        :return: None
        """
        yield self.proxyRequest()

    @web.asynchronous
    @gen.coroutine
    def head(self, *args, **kwargs):
        """
        HEAD Luna API proxy request handler.

        :param args: request args
        :param kwargs: request kwargs
        :return: None
        """
        yield self.proxyRequest()

    @web.asynchronous
    @gen.coroutine
    def get(self, *args, **kwargs):
        """
        GET Luna API proxy request handler.

        :param args: request args
        :param kwargs: request kwargs
        :return: None
        """
        yield self.proxyRequest()

    @web.asynchronous
    def options(self, *args, **kwargs):
        """
        OPTIONS Luna API proxy request handler.

        :param args: request args
        :param kwargs: request kwargs
        :return: None
        """
        self.set_status(200)
        self.finish()

    def set_default_headers(self):
        """
        Set default response headers.

        :return: None
        """
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Credentials", 'true')
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Auth-Token")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, OPTIONS, PATCH, DELETE')

    @gen.coroutine
    def proxyRequest(self):
        """
        The main proxy function. Makes request to Luna API.

        :return: None
        """
        httpClient = httpclient.AsyncHTTPClient()
        headers = self.request.headers
        headers["X-Auth-Token"] = LUNA_API_TOKEN
        url = "{}:{}/{}/".format(LUNA_API_HOST, LUNA_API_PORT, LUNA_API_API_VERSION)
        url += "/".join(self.request.uri.split("/")[2:])
        request = HTTPRequest(url,
                              body = self.request.body,
                              method = self.request.method,
                              headers = headers,
                              request_timeout = REQUEST_TIMEOUT,
                              connect_timeout = CONNECT_TIMEOUT,
                              allow_nonstandard_methods = True)
        requestResult = yield httpClient.fetch(request, raise_error = False)

        if requestResult.code == 599:
            error = generateLunaTornadoRequestError(requestResult)
            self.set_header('Content-Type', 'application/json')
            self.set_status(500)
            responseJson = {'error_code': error.errorCode, 'detail': error.description}
            self.finish(json.dumps(responseJson, ensure_ascii = False))
        self.set_status(requestResult.code)
        if requestResult.code == 304:
            return self.finish()
        contentType = requestResult.headers.get('Content-Type', None)
        self.set_status(requestResult.code)
        if contentType is not None:
            self.set_header('Content-Type', contentType)
        self.finish(requestResult.body or None)
