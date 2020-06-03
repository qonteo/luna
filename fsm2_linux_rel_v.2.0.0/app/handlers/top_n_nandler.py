from tornado import web, gen

from app.common_objects import API_VERSION
from app.common_objects import ES_CLIENT
from app.common_objects import ES_CLIENT as es
from app.handlers.schemas import TOP_N_SCHEMA
from app.task_requests import sendTask
from common.tasks import Task, TaskType
from errors.error import Error
from .base_handler import BaseHandler


class ProbabilityTopNHandler(BaseHandler):
    """
    Hit Top N tasks handler.
    """
    @web.asynchronous
    @gen.coroutine
    def post(self):
        """
        Start hit top n task handler.
        The response codes:
            202 if task was created successfully
            400 if task has not valid json
            415 if request content type is not 'application/json'
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
        if not self.validateJson(taskJson, TOP_N_SCHEMA):
            return
        taskParams = {"top_n": taskJson["top_n"], "description": "", "list_id": taskJson["list_id"]}
        if "description" in taskJson:
            taskParams["description"] = taskJson["description"]
        task = Task(TaskType.HIT_TOP_N, taskParams)
        res = yield es.putTask(task)
        if res.fail:
            return self.error(500, res.errorCode, res.description)
        res = yield sendTask(task.id)
        if res.fail:
            return self.error(500, res.errorCode, res.description)
        self.set_header("Location", "/api/{}/tasks/{}".format(API_VERSION, task.id))
        return self.success(202, {"task_id": task.id})
