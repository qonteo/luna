from typing import Dict

from tornado import gen, httpclient
from tornado.httpclient import HTTPRequest
import ujson as json
from crutches_on_wheels.utils.log import Logger


@gen.coroutine
def send_account_statistics(statistics: Dict, request_id: str, logger: Logger) -> None:
    """
    Send account statistics to other service

    :param statistics: json with stats
    :param request_id: request id
    :param logger: logger
    """
    http_client = httpclient.AsyncHTTPClient()

    request = HTTPRequest("http://127.0.0.1:6543/events",
                          body=json.dumps(statistics, ensure_ascii=False),
                          method="POST",
                          headers={"Content-Type": "application/json",
                                   "LUNA-Request-Id": request_id},
                          connect_timeout=5,
                          request_timeout=10)

    reply = yield http_client.fetch(request, raise_error=False)
    logger.debug(reply.code)
    logger.debug(reply.body.decode("utf-8"))


def setup(register_callbacks):
    """
    Registration of callbacks.

    This function must be call automatically. register_callbacks have one parameter - dict, example \
    *{"send_account_statistics": send_account_statistics}*.

    :param register_callbacks: system function for registration callbacks.
    :return: nothing
    """
    register_callbacks({"send_account_statistics": send_account_statistics})
