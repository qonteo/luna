import asyncio

from collections.abc import Mapping
import email

from websockets import WebSocketServerProtocol, InvalidOrigin, InvalidHandshake, WebSocketCommonProtocol
from websockets.handshake import check_request, build_response, accept
from websockets.http import read_request, USER_AGENT
from websockets.protocol import CONNECTING
from websockets.protocol import OPEN
from websockets.server import logger

from .api_tools import ApiError, BadRequest


class ApiWebSocketServerProtocol(WebSocketServerProtocol):
    def __init__(self, ws_handler=None, ws_server=None, **kwds):
        if ws_handler is not None:
            self.handshake_handler, handler = ws_handler
        else:
            handler = None

        super().__init__(handler, ws_server, **kwds)

    def connection_made(self, transport):
        WebSocketCommonProtocol.connection_made(self, transport)
        if self.ws_server is not None:
            # Register the connection with the server when creating the handler
            # task. (Registering at the beginning of the handler coroutine
            # creates a race condition between the task creation, which
            # schedules its execution, and the moment the handler starts running.)
            self.ws_server.register(self)

            self.handler_task = asyncio.ensure_future(
                self.handler(), loop=self.loop
            )

    @asyncio.coroutine
    def handler(self):
        # Since this method does not have a caller able to handle exceptions,
        # it attempts to log relevant ones and close the connection properly.
        try:

            try:
                path = yield from self.handshake(
                    origins=self.origins, subprotocols=self.subprotocols,
                    extra_headers=self.extra_headers)
            except Exception as exc:
                if self._is_server_shutting_down(exc):
                    response = ('HTTP/1.1 503 Service Unavailable\r\n\r\n'
                                'Server is shutting down.')
                elif isinstance(exc, InvalidOrigin):
                    response = 'HTTP/1.1 403 Forbidden\r\n\r\n' + str(exc)
                elif isinstance(exc, ApiError):
                    response = 'HTTP/1.1 {} {}\r\n\r\n'.format(exc.code, exc.describe()) + str(exc)
                elif isinstance(exc, InvalidHandshake):
                    response = 'HTTP/1.1 400 Bad Request\r\n\r\n' + str(exc)
                else:
                    logger.warning("Error in opening handshake", exc_info=True)
                    response = ('HTTP/1.1 500 Internal Server Error\r\n\r\n'
                                'See server log for more information.')
                self.writer.write(response.encode())
                raise

            try:
                yield from self.ws_handler(self, path)
            except Exception as exc:
                if self._is_server_shutting_down(exc):
                    yield from self.fail_connection(1001)
                else:
                    logger.error("Error in connection handler", exc_info=True)
                    yield from self.fail_connection(1011)
                raise

            try:
                yield from self.close()
            except Exception as exc:
                if self._is_server_shutting_down(exc):
                    pass
                else:
                    logger.warning("Error in closing handshake", exc_info=True)
                raise

        except Exception:
            # Last-ditch attempt to avoid leaking connections on errors.
            try:
                self.writer.close()
            except Exception:  # pragma: no cover
                pass

        finally:
            # Unregister the connection with the server when the handler task
            # terminates. Registration is tied to the lifecycle of the handler
            # task because the server waits for tasks attached to registered
            # connections before terminating.
            self.ws_server.unregister(self)

    @asyncio.coroutine
    def handshake(self, origins=None, subprotocols=None, extra_headers=None):
        """
        Perform the server side of the opening handshake.

        If provided, ``origins`` is a list of acceptable HTTP Origin values.
        Include ``''`` if the lack of an origin is acceptable.

        If provided, ``subprotocols`` is a list of supported subprotocols in
        order of decreasing preference.

        If provided, ``extra_headers`` sets additional HTTP response headers.
        It can be a mapping or an iterable of (name, value) pairs. It can also
        be a callable taking the request path and headers in arguments.

        Returns the URI of the request.

        """
        # Read handshake request.
        try:
            path, headers = yield from read_request(self.reader)
        except ValueError as exc:
            raise InvalidHandshake("Malformed HTTP message") from exc

        self.request_headers = headers
        self.raw_request_headers = list(headers.raw_items())

        get_header = lambda k: headers.get(k, '')
        key = check_request(get_header)

        if origins is not None:
            origin = get_header('Origin')
            if not set(origin.split() or ['']) <= set(origins):
                raise InvalidOrigin("Origin not allowed: {}".format(origin))

        if subprotocols is not None:
            protocol = get_header('Sec-WebSocket-Protocol')
            if protocol:
                client_subprotocols = [p.strip() for p in protocol.split(',')]
                self.subprotocol = self.select_subprotocol(
                    client_subprotocols, subprotocols)

        headers = []
        set_header = lambda k, v: headers.append((k, v))
        set_header('Server', USER_AGENT)
        if self.subprotocol:
            set_header('Sec-WebSocket-Protocol', self.subprotocol)
        if extra_headers is not None:
            if callable(extra_headers):
                extra_headers = extra_headers(path, self.raw_request_headers)
            if isinstance(extra_headers, Mapping):
                extra_headers = extra_headers.items()
            for name, value in extra_headers:
                set_header(name, value)
        build_response(set_header, key)

        self.response_headers = email.message.Message()
        for name, value in headers:
            self.response_headers[name] = value
        self.raw_response_headers = headers

        yield from self.handshake_handler(self, path)

        # Send handshake response. Since the status line and headers only
        # contain ASCII characters, we can keep this simple.
        response = ['HTTP/1.1 101 Switching Protocols']
        response.extend('{}: {}'.format(k, v) for k, v in headers)
        response.append('\r\n')
        response = '\r\n'.join(response).encode()
        self.writer.write(response)

        assert self.state == CONNECTING
        self.state = OPEN
        self.opening_handshake.set_result(True)

        return path

    def accept_handshake(self, headers):
        headers = {
            k.lower(): v
            for k, v in headers.items()
        }

        get_header = lambda k: headers.get(k.lower(), '')
        try:
            key = check_request(get_header)
        except InvalidHandshake as ex:
            raise BadRequest(description=str(ex))

        response = ['HTTP/1.1 101 Switching Protocols']
        response.extend(
            '{}: {}'.format(k, v) for k, v in (
                ('Upgrade', 'WebSocket'),
                ('Connection', 'Upgrade'),
                ('Sec-WebSocket-Accept', accept(key))
            )
        )
        response.append('\r\n')
        response = '\r\n'.join(response).encode()
        self.writer.write(response)

        assert self.state == CONNECTING
        self.state = OPEN
        self.opening_handshake.set_result(True)

    @classmethod
    def continue_request(cls, transport, headers):
        ws = cls()
        transport.set_protocol(ws)
        ws.connection_made(transport)
        ws.accept_handshake(headers)
        return ws
