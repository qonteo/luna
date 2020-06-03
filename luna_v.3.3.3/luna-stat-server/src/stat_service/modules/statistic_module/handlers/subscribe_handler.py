import ujson as json
from logging import getLogger

import asyncio
from voluptuous import Schema, Exclusive, In, Coerce, Invalid
from voluptuous.humanize import humanize_error
from websockets import ConnectionClosed

from common.api_tools import ClassHandler, BadRequest, ApiWebSocketServerProtocol
from common.flattenizer import FlattenizerMapper


log = getLogger('ss.stat_module.handler.subscribe')


class SocketNotifier(object):
    def __init__(self, socket):
        self._socket = socket

    async def notify(self, client_id, event_type, timestamp, message):
        log.debug(f'Notify client {client_id} on event "{event_type}" in {timestamp}')

        def cut_account_id(message):
            """
            "account_id" information is private
            :param message: to pop from
            :return:
            """
            message.pop('account_id', None)
            return message

        try:
            await self._socket.send(
                json.dumps(cut_account_id(message))
            )
        except ConnectionClosed:
            pass


class SubscribeHandler(ClassHandler):
    """
    Handler for the subscribe request
    """
    def __init__(self):
        self.auth_service = None
        self.ed_service = None

    def initialize(self, auth_service=None, ed_service=None, **kwargs):
        """
        Method to setup
        :param auth_service: luna api auth service
        :param ed_service: service to send filterred messages
        :param kwargs: garbage
        :return:
        """
        self.auth_service = auth_service
        self.ed_service = ed_service

    async def get(self, request):
        """
        GET request handler, upgrades connection and connects via WebSockets after aithorization
        :param request: request object
        :return:
        """
        try:
            query = QUERY_MODEL_MAPPER.getter(request.query).extract()
        except Invalid as err:
            log.info(f'Dropping "{request.path}" with 400 (Malformed query "{humanize_error(query, err)})"')
            raise BadRequest(description=f'(Malformed query: {humanize_error(query, err)})')

        account_id = await self.auth_service.check_user_authorized_by_request(
            request.query, request.headers, request.cookies
        )

        log.debug(f'Processing subscription request for {account_id} with params {query}')

        async with await request.upgrade_connection() as ws:
            handler = SocketNotifier(ws)
            async with await self.ed_service.subscribe(
                account_id, handler, filters=query
            ):
                await ws.connection_closed


# mapper to rename filters and verify its formats
QUERY_MODEL_MAPPER = FlattenizerMapper(
    {
        'observe':   'observe',
        'event_type': (In(['match', 'extract']), 'event_type'),
        'min_similarity': (Coerce(float), 'similarity__gt'),
        'match_list': 'list',
        'gender': (In(['male', 'female']), 'gender'),
        'min_age': (Coerce(float), 'age__gt'),
        'max_age': (Coerce(float), 'age__lt'),
        'min_glasses': (Coerce(float), 'glasses__gt'),
        'max_glasses': (Coerce(float), 'glasses__lt'),
    }
)
