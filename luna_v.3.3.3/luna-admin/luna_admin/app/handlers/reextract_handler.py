"""
Reextract module.
"""
from tornado import gen
from typing import Generator

from app.handlers.schemas import REEXTRACT_DESCRIPTORS_LIST_SCHEMA
from app.long_tasks.tasks import ReExtractTask
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.utils.timer import timer
from app.handlers.base_handler import BaseHandlerWithAuth
from configs.config import LUNA_CORE_REEXTRACT_ORIGIN, LUNA_CORE_ORIGIN


class ReExtractHandler(BaseHandlerWithAuth):
    """
    Reextract handler.
    """

    @timer
    @BaseHandlerWithAuth.requestExceptionWrap
    def post(self) -> None:
        """
        Create new reextract task

        .. http:post:: /reextract

            **Example request**:

                :reqheader Authorization: basic authorization

                .. sourcecode:: http

                    POST /reextract HTTP/1.1
                    Accept: application/json

                .. json:object:: task
                    :showexample:

                    :property descriptors: task
                    :proptype descriptors: _list_(uuid4)


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

            :statuscode 201: task is created.
            :statuscode 400: Bad json
            :statuscode 500: internal server error

        """
        self.task = None

        if LUNA_CORE_REEXTRACT_ORIGIN == LUNA_CORE_ORIGIN:
            self.set_status(403)
            self.write({"error_code": 10, "detail": "LUNA Core service is the same with LUNA Core for re-extracting "
                                                    "descriptors"})
            return self.finish()

        strJson = self.request.body
        if len(strJson) == 0:
            self.task = ReExtractTask(self.dbAdminContext, requestId=self.requestId)
        else:
            try:
                inputJson = self.getInputJson()
                self.validateJson(inputJson, REEXTRACT_DESCRIPTORS_LIST_SCHEMA)
                descriptors = inputJson["descriptors"]
                self.task = ReExtractTask(self.dbAdminContext, descriptors, "list descriptors",
                                          requestId=self.requestId)
            except ValueError:
                return self.error(400, error=Error.RequestNotContainsJson)
        self.set_header("Location", "/tasks/{}".format(self.task.taskId))
        return self.success(201, outputJson={"task_id": self.task.taskId})

    @timer
    @gen.coroutine
    def on_finish(self) -> Generator[None, None, None]:
        """
        Start execute task
        """
        if self.request.method == "POST":
            if hasattr(self, "task") and self.task is not None:
                if self.task.descriptors is None:
                    yield self.task.reExtractAllDescriptorAttribute(self.task.taskId)
                else:
                    yield self.task.reExtractDescriptorsList(self.task.taskId, self.task.descriptors)
