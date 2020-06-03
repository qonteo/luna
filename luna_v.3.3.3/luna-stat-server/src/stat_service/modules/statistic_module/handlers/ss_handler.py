from logging import getLogger

from voluptuous import Invalid, Match
from voluptuous.humanize import humanize_error

from common.api_tools import ClassHandler, BadRequest
from common.flattenizer import FlattenizerMapper

from ..services.stat_service import StatService


log = getLogger('ss.stat_module.handler.events')


class StatHandler(ClassHandler):
    """
    Statistics handler
    """
    def __init__(self):
        self.influx_db = None
        self.auth_service = None
        self.stat_service = None

    def initialize(self, influx_client=None, auth_service=None, stat_service=None, **kwargs):
        """
        Method to setup
        :param influx_client: request parser
        :param auth_service: luna api auth service
        :param stat_service: influx async client
        :param kwargs: garbage
        :return:
        """
        self.influx_db = influx_client
        self.auth_service = auth_service
        self.stat_service = stat_service

    async def get(self, request):
        """
        GET request handler
        :param request: request object
        :return:
        """
        account_id = await self.auth_service.check_user_authorized_by_request(
            request.query, request.headers, request.cookies
        )
        try:
            query = request.query
            if 'observe' in query:
                query.update({'authorization__mp': query.pop('observe')})
            parameters = QUERY_MODEL_MAPPER.getter(query).extract()
        except Invalid as err:
            log.info(f'Dropping "{request.path}" with 400 (Malformed query "{humanize_error(parameters, err)})"')
            raise BadRequest(description=f'(Malformed query: {humanize_error(parameters, err)})')

        log.debug(f'Processing stat request for {account_id} with params {parameters}')

        return request.Response(
            code=200, json=await self.stat_service.query(
                account_id, **parameters
            )
        )


def _process_fields(fields):
    return [
        f for f in (
            f.strip() for f in fields.split(',')
        ) if f.isidentifier()
    ]


QUERY_MODEL_MAPPER = FlattenizerMapper(
    dict(
        **{
            'group_step': (Match(r'^-?(\d+)(u|s|m|h|d|w)$'), 'group_step', '1h'),
            'aggregator': (Match(r'^((count)|(min)|(max)|(mean))$'), 'aggregator', 'max'),
            'gender': 'gender',
            'fields': (_process_fields, 'fields')
        },
        **{
            f: f
            for f in StatService.get_allowed_filters()
        }
    )
)
