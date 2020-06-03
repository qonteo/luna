from tornado import httpclient, gen
from tornado.httpclient import HTTPRequest
from configs.config import REQUEST_TIMEOUT, CONNECT_TIMEOUT
from configs.comand_line_args_parser import getOptionsParser

import ujson as json
from app.common_objects import logger
from errors.error import Result, Error


@gen.coroutine
def sendTask(taskId):
    cmdOptions = getOptionsParser()

    url = "http://127.0.0.1:{}/tasks".format(cmdOptions["analytics_port"])
    http_client = httpclient.AsyncHTTPClient()
    headers = {'Content-Type': 'application/json'}
    request = HTTPRequest(url,
                          body = json.dumps({"task_id": taskId}, ensure_ascii = False),
                          method = "POST",
                          headers = headers,
                          request_timeout = REQUEST_TIMEOUT,
                          connect_timeout = CONNECT_TIMEOUT)

    reply = yield http_client.fetch(request, raise_error = False)
    if 200 <= reply.code < 300:
        return Result(Error.Success, 0)
    else:
        logger.error("failed ")
        return Result(Error.SendTaskToExecuteError, 0)
