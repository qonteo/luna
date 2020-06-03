"""
The module provides some wrappers to unify different web-server APIs, like Japronto and Sanic
"""
import ujson

import asyncio

from sanic.request import Request
from sanic.response import HTTPResponse
from sanic.websocket import WebSocketProtocol

from common.api_tools import ClassHandler, ApiWebSocketServerProtocol


#####################
# Japronto wrappers #
#####################
def init_japronto_app(application, handlers, error_handlers, context):
    for error_cls, handler in error_handlers.items():
        application.add_error_handler(error_cls, handler)

    for path, handler in handlers.items():
        if not path.startswith('/'):
            path = f'/{path}'

        if issubclass(handler, ClassHandler):
            for method, method_handler in handler.create_handlers(context).items():
                application.router.add_route(
                    path, method_handler, method=method
                )
        else:
            application.router.add_route(
                path, handler
            )


##################
# SANIC wrappers #
##################
class UpgradedConnectionContextManager(object):
    def __init__(self, app, ws):
        self.app = app
        self.task = None
        self.ws = ws

    async def __aenter__(self):
        self.task = asyncio.Task.current_task(self.app.loop)
        self.app.websocket_tasks.append(self.task)
        return self.ws

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.app.websocket_tasks.remove(self.task)

        await self.ws.close()


class UpgradableHttpProtocol(WebSocketProtocol):
    async def websocket_handshake(self, request):
        self.websocket = ApiWebSocketServerProtocol()
        self.websocket.connection_made(request.transport)
        self.websocket.accept_handshake(request.headers)
        return self.websocket


class SanicRequest(Request):
    """
    Improved sanic Request class
    """
    def Response(self, text=None, json=None, code=200, mime_type='text/plain', **kwargs):
        """
        Response constructor inside request object
        :param text: text to send
        :param json: json to send (ignored if "text" presents)
        :param code: response status_code
        :param mime_type: Content-Type header
        :param kwargs: cookies, headers, etc.
        :return: sanic HTTPResponse object
        """
        if text is not None:
            content = text
        elif json is not None:
            content = ujson.dumps(json)
            mime_type = 'application/json'
        else:
            content = ''

        return HTTPResponse(content, status=code, content_type=mime_type, **kwargs)

    @property
    def query(self):
        """
        Query property to access query parameters
        :return: query parameters {key: value} dict
        """
        return self.raw_args

    async def upgrade_connection(self):
        """
        WebSocket as context manager provider
        :return: context manager
        """
        ws = await self.transport.get_protocol().websocket_handshake(self)
        return UpgradedConnectionContextManager(self.app, ws)


def init_sanic_app(application, handlers, error_handlers, context):
    """
    Sanic configurator and runner
    :param application: sanic app object to configure
    :param handlers: {route: handler} dictionary
    :param error_handlers: {Exception: handler} dictionary
    :param context: {name: service} dictionary (e.g. redis_client or influx_client)
    :return:
    """
    application.request_class = SanicRequest
    application.websocket_protocol = UpgradableHttpProtocol

    for error_cls, handler in error_handlers.items():
        application.error_handler.add(error_cls, handler)

    for path, handler in handlers.items():
        if not path.startswith('/'):
            path = f'/{path}'

        if isinstance(handler, type) and issubclass(handler, ClassHandler):
            for method, method_handler in handler.create_handlers(context).items():
                application.router.add(
                    path, [method], method_handler
                )
        else:
            application.router.add(
                path, ['GET'], handler
            )

    application.enable_websocket()
