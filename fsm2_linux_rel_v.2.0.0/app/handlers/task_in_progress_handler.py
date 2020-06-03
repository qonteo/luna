from tornado import web, gen

from app.common_objects import API_VERSION, ES_CLIENT
from common.helpers import replaceTimeRecursively
from common.tasks import Task, TaskStatus
from errors.error import Error
from .base_handler import BaseHandler


class TasksInProgressHandler(BaseHandler):
    """
    Search tasks in progress handler.
    """
    @web.asynchronous
    @gen.coroutine
    def get(self):
        """
        Get all tasks in progress.
        The response codes:
            200 if search succeed
            500 if internal system error occurred

        :return: None
        """
        try:
            pageSize = max(min(int(self.get_query_argument("page_size", 20)), 100), 1)
        except ValueError:
            return self.error(400, Error.BadQueryParam.getErrorCode(),
                              Error.BadQueryParam.getErrorDescription().format('page_size'))
        try:
            page = max(int(self.get_query_argument("page", 1)), 1)
        except ValueError:
            return self.error(400, Error.BadQueryParam.getErrorCode(),
                              Error.BadQueryParam.getErrorDescription().format('page'))
        searchTasksFilters = ES_CLIENT.SearchTask(False, pageSize, page)
        res = yield ES_CLIENT.searchTasks(searchTasksFilters)
        if res.fail:
            return self.error(500, res.errorCode, res.description)
        return self.success(200, replaceTimeRecursively(res.value))


class TaskInProgressHandler(BaseHandler):
    """
    Get task in progress handler.
    """
    @web.asynchronous
    @gen.coroutine
    def get(self, taskId):
        """
        Get task by id.
        The response codes:
            200 if task was found by id and it is still in progress
            303 if task was found by id and it not in progress
            404 if task was not found by id
            500 if internal system error occurred

        :param taskId: task id
        :return: None
        """
        taskRes = yield ES_CLIENT.getTask(taskId)
        if taskRes.fail:
            if taskRes.error == Error.TaskNotFound:
                return self.error(404, taskRes.errorCode, taskRes.description)
            return self.error(500, taskRes.errorCode, taskRes.description)
        if "Location" in taskRes.value:
            self.set_header("Location", taskRes.value["Location"])
            self.set_status(303)
            return self.finish()
        return self.success(200, replaceTimeRecursively(taskRes.value))

    @web.asynchronous
    @gen.coroutine
    def delete(self, taskId):
        """
        Cancel a task.
        The response codes:
            204 if task was found by id and it was cancelled
            303 if task was found by id and it not in progress
            404 if task was not found by id
            500 if internal system error occurred

        :param taskId: task id
        :return: None
        """
        taskRes = yield ES_CLIENT.getTask(taskId)
        if taskRes.fail:
            if taskRes.error == Error.TaskNotFound:
                return self.error(404, taskRes.errorCode, taskRes.description)
            return self.error(500, taskRes.errorCode, taskRes.description)
        if "Location" in taskRes.value:
            self.set_header("Location", taskRes.value["Location"])
            self.set_status(303)
            return self.finish()
        task = Task.generateTaskFromDict(taskRes.value)
        task.status = TaskStatus.CANCELED.value
        deleteRes = yield ES_CLIENT.markTaskDone(task, "/api/{}/analytics/tasks/{}".format(API_VERSION, taskId))
        if deleteRes.fail:
            return self.error(500, deleteRes.errorCode, Error.InternalServerError.getErrorDescription())
        else:
            self.set_status(204)
            self.finish()
