from tornado import gen
from typing import Generator

from common.query_validators import uuid4Getter, getterGCNonLinkedFacesTaskType, getterTarget, getterTaskType
from crutches_on_wheels.utils.timer import timer
from crutches_on_wheels.errors.errors import Error
from app.long_tasks.tasks import GCNonLinkedFacesTask
from app.handlers.base_handler import BaseHandlerWithAuth


class GCHandler(BaseHandlerWithAuth):
    """
    GC handler.

    Attributes:
        task(GCNonLinkedFacesTask): new task
    """

    def initialize(self) -> None:
        """
        Add to instance attribute task
        """
        self.task = None
        super().initialize()

    @BaseHandlerWithAuth.requestExceptionWrap
    def post(self):
        """
        Create new task for remove not linked faces

        .. http:post:: /gc


            :query task_type: required param, only descriptors at the moment
            :query target: target for task ("all", "account")
            :query target_id: account id if target account

            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 201 Created
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d
                    Location: /tasks/12

                .. json:object:: task
                    :showexample:

                    :property task_id: task
                    :proptype task_id: integer

            Message error is returned in format :json:object:`server_error`.

            :statuscode 201: task has been created
            :statuscode 400: Bad query param
            :statuscode 500: internal server error

        """
        self.getQueryParam("task_type", getterGCNonLinkedFacesTaskType, require=True)

        target = self.getQueryParam("target", getterTarget, require=True)

        targetId = self.getQueryParam("target_id", uuid4Getter)

        self.task = GCNonLinkedFacesTask(self.dbAdminContext, self.dbApiContext, target, targetId)
        self.set_header("Location", "/tasks/{}".format(self.task.taskId))
        self.success(201, outputJson={"task_id": self.task.taskId})

    @timer
    @gen.coroutine
    def on_finish(self):
        """
        Start execute task
        """
        if self.request.method == "POST":
            if hasattr(self, "task") and self.task is not None:
                yield self.task.senderToExecute(**self.task.kwargs)


class TasksHandler(BaseHandlerWithAuth):
    """
    Tasks handler.
    """

    @BaseHandlerWithAuth.requestExceptionWrap
    def get(self) -> None:
        """
        Get Tasks.

        .. http:get:: /tasks


            :query page: page count, default 1
            :query page_size: page size, default 10

            **Example request**:

                :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json

                .. json:object:: tasks
                    :showexample:

                    :property tasks: task
                    :proptype tasks: _list_(task_type)
                    :property task_count: task count
                    :proptype task_count: task_count

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: ok
            :statuscode 400: Bad query param
            :statuscode 500: internal server error

        """
        page, pageSize = self.getPagination()
        taskType = self.getQueryParam("task_type", getterTaskType)
        tasks = self.dbAdminContext.getTasks(page, pageSize, taskType)
        taskCount = self.dbAdminContext.getCountTasks(taskType)
        return self.success(200, outputJson={"tasks": tasks, "task_count": taskCount})


class TaskHandler(BaseHandlerWithAuth):
    """
    Task handler.
    """

    @BaseHandlerWithAuth.requestExceptionWrap
    def get(self, taskId: int) -> None:
        """
        Get Tasks.

        .. http:get:: /tasks/{taskId}

            :param taskId: task id

            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json


                Output account will be represent in  :json:object:`task_type`

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: ok
            :statuscode 400: Bad query param
            :statuscode 404: Task not found
            :statuscode 500: internal server error

        """
        task = self.dbAdminContext.getGCTask(taskId)
        if task is None:
            return self.error(404, error=Error.TaskNotFound)
        return self.success(200, outputJson=task)

    @BaseHandlerWithAuth.requestExceptionWrap
    def delete(self, taskId: int) -> None:
        """
        Stop task.

        .. http:delete:: /tasks/{taskId}

            :param taskId: task id

            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 204 Stoped
                    Vary: Accept
                    Content-Type: application/json


                Output account will be represent in  :json:object:`task_type`

            Message error is returned in format :json:object:`server_error`.

            :statuscode 204: stoped
            :statuscode 400: Bad query param
            :statuscode 404: Task not found
            :statuscode 500: internal server error

        """
        self.dbAdminContext.finishTask(taskId, False)
        self.success(204)


class TaskErrorsHandler(BaseHandlerWithAuth):
    """
    Task errors handler.
    """

    @BaseHandlerWithAuth.requestExceptionWrap
    def get(self, taskId: int) -> None:
        """
        Get error of the a task.

        .. http:get:: /tasks/{taskId}/errors

            :param taskId: task id

            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json

                .. json:object:: error

                    :property error_time:  error time
                    :proptype error_time: iso8601
                    :proptype message: error details
                    :property code:  error code
                    :proptype code: integer
                    :property id:  error number
                    :proptype id: integer
                    :property task_type:  type of task
                    :proptype task_type: _enum_(removing old descriptors)_(re-extract descriptors)

                .. json:object:: errors
                    :showexample:

                    :property errors:  The name of current series
                    :proptype errors: _list_(:json:object:`error`)
                    :property error_count:  count of errors
                    :proptype error_count: integer

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: ok
            :statuscode 400: Bad query param
            :statuscode 404: Task not found
            :statuscode 500: internal server error

        """
        page, pageSize = self.getPagination()
        task = self.dbAdminContext.getGCTask(taskId)
        if task is None:
            return self.error(404, error=Error.TaskNotFound)
        errors = self.dbAdminContext.prepareErrorOfTaskToRender(taskId, page, pageSize)
        return self.success(200, outputJson=errors)
