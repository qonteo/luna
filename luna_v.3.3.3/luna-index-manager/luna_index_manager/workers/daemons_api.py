"""
Module realize two request functions to work with matchers-daemons (getStateOfTask, startTask).
"""
from typing import Generator, Tuple

from logbook import Logger
from tornado import gen, httpclient, escape
from tornado.httpclient import HTTPRequest, HTTPResponse

from configs.config import REQUEST_TIMEOUT, CONNECT_TIMEOUT
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.utils.timer import timer
from workers.task import IndexTask


def getReason(response: HTTPResponse) -> str:
    """
    Get reason of failed request.

    Args:
        response: failed response

    Returns:
        string  with error
    """
    if response.code == 599:
        if type(response.error) == ConnectionRefusedError:
            reason = "connection refused"
        elif type(response.error) == ConnectionAbortedError:
            reason = "connection aborted"
        elif type(response.error) == TimeoutError:
            reason = "timeout error"
        else:
            reason = str(response.error)
    else:
        try:
            reason = response.body.decode("utf-8")
        except ValueError:
            reason = "unknown"
    return reason


class DaemonContext:

    def __init__(self, logger: Logger):
        self.logger = logger

    def printError(self, response, resource, reason, body=None):

        self.logger.error("resource: {}".format(resource))
        self.logger.error("body: {}".format(body))
        self.logger.error("status code: {}".format(response.code))
        self.logger.error("reason: {}".format(reason))

    @timer
    @gen.coroutine
    def getStateOfTask(self, task: IndexTask, daemonEndPoint: str, daemonTaskId: str, resource: str) -> \
            Generator[None, None, Tuple[str, dict]]:
        """
        Get state of the task

        Args:
            task: create index task.
            daemonEndPoint: daemon EndPoint
            daemonTaskId: task id
            resource: "restart_tasks" or "upload_tasks"
        Returns:
            state and response json

        Raises:
            VLException: if request failed
        """
        http_client = httpclient.AsyncHTTPClient()
        url = "{}/{}/{}".format(daemonEndPoint, resource, daemonTaskId)
        headers = {"LUNA-Request-Id": task.taskRequestId}
        request = HTTPRequest(url, method="GET", headers=headers, request_timeout=REQUEST_TIMEOUT,
                              connect_timeout=CONNECT_TIMEOUT)

        reply = yield http_client.fetch(request, raise_error=False)
        if reply.code < 400:
            repJson = escape.json_decode(reply.body)
            state = repJson["state"]
            return state, repJson

        reason = getReason(reply)
        self.printError(reply, url, reason)

        if resource == "upload_tasks":
            error = Error.formatError(Error.FailedUploadIndex, task.generation, daemonEndPoint, reason)
        else:
            error = Error.formatError(Error.FailedReloadIndex, task.generation, daemonEndPoint, reason)
        raise VLException(error)

    @timer
    @gen.coroutine
    def startTask(self, task: IndexTask, body: str, resource: str, daemonEndPoint: str) -> Generator[None, None, str]:
        """
        Send upload index or restart indexes request to daemon

        Args:
            task: create index task.
            daemonEndPoint: daemon EndPoint
            body: body
            resource: "restart_tasks" or "upload_tasks"
        Returns:
            task id
        Raises:
            VLException: if request failed
        """
        http_client = httpclient.AsyncHTTPClient()
        url = "{}/{}".format(daemonEndPoint, resource)
        headers = {"LUNA-Request-Id": task.taskRequestId, "Content-Type": "application/json"}
        request = HTTPRequest(url, body=body, method="PUT", headers=headers, request_timeout=REQUEST_TIMEOUT,
                              connect_timeout=CONNECT_TIMEOUT)

        reply = yield http_client.fetch(request, raise_error=False)
        if reply.code < 400:
            repJson = escape.json_decode(reply.body)
            return repJson["task_id"]

        reason = getReason(reply)
        self.printError(reply, url, reason, body)
        if resource == "upload_tasks":
            error = Error.formatError(Error.FailedUploadIndex, task.generation, daemonEndPoint, reason)
        else:
            error = Error.formatError(Error.FailedReloadIndex, task.generation, daemonEndPoint, reason)
        raise VLException(error)
