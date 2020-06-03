from tornado import web, gen

from app.common_objects import API_VERSION
from app.common_objects import ES_CLIENT as es
from app.handlers.schemas import CROSS_MATCHER_SCHEMA
from app.task_requests import sendTask
from common.helpers import convertRfc3339ToTimestampMillis, replaceTimeRecursively
from common.tasks import Task, TaskType
from errors.error import Error
from .base_handler import BaseHandler


class CrossMatcherHandler(BaseHandler):
    """
    Handler for cross-matching tasks.
    """
    @web.asynchronous
    @gen.coroutine
    def post(self):
        """
        The only allowed method.
        The response codes:
            202 if task was created successfully
            400 if task parameters have wrong format
            415 if content type is not 'application/json'
            500 if internal system error occurred

        :return: None
        """
        contentType = self.request.headers.get("Content-Type", None)
        if contentType != 'application/json':
            error = Error.BadContentType
            self.error(415, error.getErrorCode(), error.getErrorDescription())

        taskJson = self.loads()
        if taskJson is None:
            return

        if not self.validateJson(taskJson, CROSS_MATCHER_SCHEMA):
            return

        replaceTimeRecursively(taskJson, convertRfc3339ToTimestampMillis)

        task = Task(TaskType.CROSS_MATCHER, taskJson)
        res = yield es.putTask(task)
        if res.fail:
            return self.error(500, res.errorCode, res.description)
        res = yield sendTask(task.id)
        if res.fail:
            return self.error(500, res.errorCode, res.description)
        self.set_header("Location", "/api/{}/tasks/{}".format(API_VERSION, task.id))
        return self.success(202, {"task_id": task.id})
