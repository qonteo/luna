"""
LPS service authorization stub.
The method returns the user authorization token's ID (UUID)
"""


from logging import getLogger
from uuid import UUID

from sanic import Sanic as Application

from common.api_tools.webserver_utils import init_sanic_app


log = getLogger('ss.lps_stub')


async def handle_check_user_auth(request, version):
    """
    Authorization request handler (used to work without LPS)
    :param request: request object with one of authorization headers
    :return: 401 if wrong auth is given, else 200 with some "accont_id"
    """
    basic_pair = request.headers.get('Authorization')
    auth_token = request.headers.get('X-Auth-Token')
    if basic_pair is not None:
        if not basic_pair.lower().startswith('basic '):
            return request.Response(code=401)
        try:
            res = UUID(int=hash(basic_pair[len('basic '):]))
        except ValueError:
            return request.Response(code=401)
    elif auth_token is not None:
        res = auth_token
    else:
        return request.Response(code=401)

    log.debug(f'Client {res} authorized with "{basic_pair or auth_token}"')
    return request.Response(code=200, text=res)


def main(settings):
    """
    The initial module 
    :param settings: host and port to run at
    :return:
    """
    app = Application()

    init_sanic_app(app, {'/<version:int>/login': handle_check_user_auth}, {}, {})

    app.run(host=settings.host, port=settings.port)
