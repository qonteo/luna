import asyncio
from logging import getLogger

import aiohttp
from sanic import Sanic as Application
from uvloop import EventLoopPolicy

from common.api_tools import ApiError
from common.api_tools.webserver_utils import init_sanic_app

from common.async_influxdb import AsyncInfluxDBClient
from stat_service.utils import create_aioredis

from stat_service.modules.statistic_module.handlers import HANDLERS
from stat_service.modules.statistic_module.services.ed_service import EventDeliveryService
from stat_service.modules.statistic_module.services.lps_auth_service import LPSUserAuthService
from stat_service.modules.statistic_module.services.stat_service import StatService


log = getLogger('ss.stat_module')


def add_demo():
    """
    Add demo routes to all enother
    :return:
    """
    from os import path

    root_dir = path.join(path.dirname(__file__), *'../../../..'.split('/'))

    def create_handler(filename, content_type='text/html'):
        """
        Demo page handler constructor
        :param filename: filename to share
        :param content_type:
        :return:
        """
        with open(path.join(root_dir, 'demo', filename)) as f:
            content = f.read()

        def handle(request):
            """
            Demo page handler
            :param request:
            :return:
            """
            return request.Response(content, mime_type=content_type)

        return handle

    return {
        resource: create_handler(name, ct)
        for resource, name, ct in (
            ('demo', 'demo.html', 'text/html'),
            ('raml', 'raml.html', 'text/html'),
            ('ss_lib.js', 'ss_lib.js', 'application/json')
        )
    }


def handle_api_error(request, exception: ApiError):
    log.info(f'{request.path} [{request.method}] {exception.code}: {exception.describe()}')
    return request.Response(**exception.as_response())


def main(settings):
    """
    Init sm
    :param settings:
    :return:
    """
    asyncio.set_event_loop_policy(EventLoopPolicy())
    loop = asyncio.get_event_loop()
    application = Application()

    with aiohttp.ClientSession(loop=loop) as session:
        redis = loop.run_until_complete(
            asyncio.ensure_future(
                create_aioredis(
                    settings.redis_connection_url, loop=loop
                ), loop=loop
            )
        )

        ed_service = EventDeliveryService(redis, loop=loop)
        loop.create_task(ed_service.start())

        influx = AsyncInfluxDBClient.from_DSN(
            settings.influx_connection_url, session=session, timeout=settings.http_timeout
        )
        auth_service = LPSUserAuthService(
            loop, settings.lps_url+'/login', session, cookie_secret=settings.cookie_secret
        )
        stat_service = StatService(influx)

        context = {
            'influx_client': influx,
            'auth_service': auth_service,
            'stat_service': stat_service,
            'ed_service': ed_service
        }

        if settings.run_demo:
            HANDLERS.update(add_demo())

        init_sanic_app(
            application, HANDLERS, {ApiError: handle_api_error}, context
        )

        application.run(
            host=settings.host, port=settings.port, loop=loop
        )
