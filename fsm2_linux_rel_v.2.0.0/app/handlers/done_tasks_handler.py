from tornado import web, gen

from app.common_objects import logger
from app.common_objects import ES_CLIENT as es
from common.helpers import replaceTimeRecursively, nestedGetter
from errors.error import Error
from app.handlers.base_handler import BaseHandler


SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["done", "canceled", "failed"],
        },
        "task_type": {
            "type": "string",
            "enum": ["hit_top_n", "report", "linking", "cross_matching", "clusterization"],
        },
        "description": {
            "type": "string"
        },
        "page_size": {
            "type": "integer"
        },
        "page": {
            "type": "integer"
        }
    },
    "required": ["task_type"]
}


class DoneTasksHandler(BaseHandler):
    """
    Get done tasks list.
    """
    @gen.coroutine
    def get(self):
        """
        Get done task list with pagination.
        Response status codes:
            200 if search succeed
            500 if internal system error occurred

        :return: None
        """
        status = self.get_argument("status", None)
        taskType = self.get_argument("task_type", None)
        description = self.get_argument("description", None)
        page = self.get_argument("page", 1)
        try:
            page = max(int(page), 0)
        except ValueError:
            logger.debug("'page' parameter has wrong value {}".format(page))
            self.error(400, Error.BadQueryParam.getErrorCode(), Error.BadQueryParam.getErrorDescription().format(
                "'page' parameter has wrong value '{}'".format(page)))
            return

        pageSize = self.get_argument("page_size", 20)
        try:
            pageSize = max(0, min(int(pageSize), 100))
        except ValueError:
            logger.debug("'page' parameter has wrong value {}".format(page))
            self.error(400, Error.BadQueryParam.getErrorCode(), Error.BadQueryParam.getErrorDescription().format(
                "'page_size' parameter has wrong value '{}'".format(pageSize)))
            return

        filters = {
            k: v
            for k, v in (
                ("status", status),
                ("task_type", taskType),
                ("description", description),
                ("page_size", pageSize),
                ("page", page)
            ) if v is not None
        }
        if not self.validateQueries(filters, SCHEMA):
            return
        searchTask = es.SearchTask(True, **filters)
        searchRes = yield es.searchTasks(searchTask)
        if searchRes.fail:
            return self.error(500, searchRes.errorCode, searchRes.description)
        return self.success(200, replaceTimeRecursively(searchRes.value))


class DoneTaskHandler(BaseHandler):
    """
    Get or delete a done task.
    """
    @web.asynchronous
    @gen.coroutine
    def get(self, taskId):
        """
        Get done task by its id.
        Response status codes:
            200 if task was found
            404 if task was not found
            500 if internal system error occurred

        :param taskId: task id
        :return: None
        """
        taskRes = yield es.getDoneTask(taskId)
        if taskRes.fail:
            if taskRes.error == Error.TaskNotFound:
                return self.error(404, taskRes.errorCode, taskRes.description)
            return self.error(500, taskRes.errorCode, taskRes.description)

        location = nestedGetter(taskRes.value, ['result', 'success', "Location"])
        if location is not None:
            self.set_header("Location", location)
            self.set_status(303)
            return self.finish()
        return self.success(200, replaceTimeRecursively(taskRes.value))

    @web.asynchronous
    @gen.coroutine
    def delete(self, taskId):
        """
        Delete done task by its id.
        Response status codes:
            204 if task was deleted
            404 if task was not found
            500 if internal system error occurred

        :param taskId: task id
        :return: None
        """
        deleteRes = yield es.deleteDoneTask(taskId)
        if deleteRes.fail:
            if deleteRes.error == Error.TaskNotFound:
                return self.error(404, deleteRes.errorCode, deleteRes.description)
            return self.error(500, deleteRes.getErrorCode(), Error.InternalServerError.getErrorDescription())
        else:
            self.set_status(204)
            self.finish()
