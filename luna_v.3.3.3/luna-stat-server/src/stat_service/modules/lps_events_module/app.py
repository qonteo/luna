import asyncio
import aiohttp
import uvloop
from redis import Redis
from logging import getLogger

from sanic import Sanic as Application

from common.api_tools.webserver_utils import init_sanic_app
from common.async_influxdb import AsyncInfluxDBClient
from common.api_tools import ApiError

from stat_service.modules.lps_events_module.handlers import HANDLERS

log = getLogger('ss.lps_events_module')


def handle_api_error(request, exception: ApiError):
    log.info(f'{request.path} [{request.method}] {exception.code}: {exception.describe()}')
    return request.Response(**exception.as_response())


def main(settings):
    """
    The function initializes LPS event module forever
    :param settings: settings object
    :return:
    """
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()

    application = Application()

    redis_client = Redis.from_url(settings.redis_connection_url)
    session = aiohttp.ClientSession(loop=loop)
    influx = AsyncInfluxDBClient.from_DSN(
        settings.influx_connection_url, session=session
    )

    context = {
        'redis_client': redis_client,
        'influx_client': influx
    }

    init_sanic_app(application, HANDLERS, {ApiError: handle_api_error}, context)

    application.run(host=settings.host, port=settings.port, loop=loop)

    session.close()
