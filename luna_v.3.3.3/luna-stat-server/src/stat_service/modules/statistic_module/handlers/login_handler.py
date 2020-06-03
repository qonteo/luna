from logging import getLogger
from voluptuous.humanize import humanize_error

from common.api_tools import ClassHandler, ApiError
from common.secure_cookies.cookies import create_signed_value, decode_signed_value

log = getLogger('ss.stat_module.handler.login')


class LoginHandler(ClassHandler):
    """
    Statistics handler
    """

    def __init__(self):
        self.auth_service = None

    def initialize(self, auth_service, **kwargs):
        """
        Method to setup
        :param auth_service: LUNA API authorization service
        :param kwargs: garbage
        :return:
        """
        self.auth_service = auth_service

    async def post(self, request):
        """
        POST request handler - setup cookie
        :param request: request object
        :return:
        """
        basic_pair = request.headers.get('Authorization') or request.query.get('basic', None)
        account_id = await self.auth_service.check_user_authorized(basic_pair=basic_pair)
        if not isinstance(account_id, ApiError):
            reply = request.Response(code=201, text='Authorized')
            reply.cookies['Authorization'] = create_signed_value(self.auth_service._cookie_secret, 'Authorization',
                                                                 basic_pair).decode()
            log.debug(f'Processing {request.path} [{request.method}] with 201 <cookie within> for {basic_pair}')
            return reply
        log.info(f'Dropping "{request.path}" [{request.method}] with 400 "{account_id.description}"')
        raise account_id

    async def get(self, request):
        """
        GET request handler - watch cookie status
        :param request:
        :return:
        """
        if 'Authorization' in request.cookies:
            basic_pair = decode_signed_value(self.auth_service._cookie_secret, 'Authorization',
                                             request.cookies['Authorization'])
            if basic_pair is not None:
                basic_pair = basic_pair
                account_id = await self.auth_service.check_user_authorized(basic_pair=basic_pair)

                log.info(f'Processing {request.path} [{request.method}] with 200 "{account_id}"')
                return request.Response(code=200, text=account_id)
            log.info(f'Dropping {request.path} [{request.method}] with 400  "Cookie is corrupted"')
            return request.Response(code=401, text='Cookie is corrupted')
        log.info(f'Dropping {request.path} [{request.method}] with 400 "Cookie not found"')
        return request.Response(code=401, text='Cookie not found')

    async def delete(self, request):
        """
        DELETE request handler - remove cookie
        :param request:
        :return:
        """
        reply = request.Response(code=204)
        if 'Authorization' in request.cookies:
            del reply.cookies['Authorization']
        log.debug(f'Processing {request.path} [{request.method}] with 204')
        return reply
