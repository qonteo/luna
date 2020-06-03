"""
Internal task handler
"""
from tornado import escape, gen
from app.admin_db.db_context import TaskType
from luna_admin.task_workers.handlers.base_handler import BaseHandler
from luna_admin.task_workers.queue.consumers import REEXTRACT_QUEUE, DESCRIPTOR_GC_QUEUE
from task_workers.worker_task import Task
from time import time
from uuid import uuid4


class TaskHandler(BaseHandler):
    """
    Internal task handler
    """

    @BaseHandler.coRequestExceptionWrap
    @gen.coroutine
    def post(self):
        """
        Create internal task.

        .. http:get:: /task

            :reqheader Authorization: basic authorization

            **Example request**:

                .. json:object:: internal_task
                    :showexample:

                    :property target:  all or id of target
                    :proptype target: _enum_(all)_(uuid4)
                    :property task_id:  task id
                    :proptype task_id: integer
                    :property subtask:  subtask number
                    :proptype subtask: integer

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
        def getTaskRequestId() -> str:
            """
            Generate request Id for current task
            Returns:
                request id
            """
            requestId = "{},{}".format(int(time()), str(uuid4()))
            self.logger.info(
                'Created Task with requestId \'{}\' from base requestId \'{}\''.format(requestId, self.requestId))
            return requestId

        task = escape.json_decode(self.request.body)
        if task["task_type"] == TaskType.descriptorsGC.value:
            yield DESCRIPTOR_GC_QUEUE.putTask(Task(task, getTaskRequestId()))
        elif task["task_type"] == TaskType.reExtractGC.value:
            yield REEXTRACT_QUEUE.putTask(Task(task, getTaskRequestId()))
        else:
            return self.error(400, 30000, "bad task type")
        return self.success(201)
