import os
from tornado import web, gen
from tornado.web import StaticFileHandler

from app.common_objects import ES_CLIENT as es, API_VERSION
from app.handlers.schemas import REPORTER_SCHEMA
from app.task_requests import sendTask
from common.tasks import Task, TaskType
from configs.config import USE_LATEX
from errors.error import Error
from .base_handler import BaseHandler


class ReporterHandler(BaseHandler):
    """
    Report maker handler.
    """
    @web.asynchronous
    @gen.coroutine
    def post(self):
        """
        Make report handler.
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
            return self.error(415, error.getErrorCode(), error.getErrorDescription())

        taskJson = self.loads()
        if taskJson is None:
            return

        if not self.validateJson(taskJson, REPORTER_SCHEMA):
            return

        if taskJson['format'] == 'pdf' and not USE_LATEX:
            err = Error.Forbidden
            return self.error(403, err.getErrorCode(), err.getErrorDescription().format("LaTeX"))

        task = Task(TaskType.REPORTER, taskJson)
        res = yield es.putTask(task)
        if res.fail:
            return self.error(500, res.errorCode, res.description)

        res = yield sendTask(task.id)
        if res.fail:
            return self.error(500, res.errorCode, res.description)

        self.set_header("Location", "/api/{}/tasks/{}".format(API_VERSION, task.id))
        return self.success(202, {"task_id": task.id})


class ReporterStaticHandler(StaticFileHandler):
    @classmethod
    def get_absolute_path(cls, root, path):
        """
        Absolute path getter for report file.

        :param root: reporter storage root directory
        :param path: report task id
        :return: absolute report path (tornado app will return 404 if file was not found in given path)
        """
        for report_type in ('.zip', '.pdf'):
            filename = os.path.join(root, path + report_type)
            if os.path.exists(filename):
                break
        return os.path.abspath(filename)

    @web.asynchronous
    def options(self, *args, **kwargs):
        """
        Options request handler.

        :param args: request args
        :param kwargs: request kwargs
        :return: None
        """
        self.set_status(200)
        self.finish()

    def set_default_headers(self):
        """
        Set default headers.

        :return: None
        """
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Credentials", 'true')
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Auth-Token")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, OPTIONS, PATCH, DELETE')

    @web.asynchronous
    def delete(self, path):
        """
        Delete the created report.
        The response codes:
            202 if task was created successfully
            400 if task parameters have wrong format
            415 if content type is not 'application/json'
            500 if internal system error occurred

        :param path:
        :return: None
        """
        for report_type in ('.zip', '.pdf'):
            filename = os.path.join(self.root, path + report_type)
            if os.path.exists(filename):
                os.remove(filename)
                self.set_status(204)
                break
        else:
            self.set_status(404)
        self.finish()
