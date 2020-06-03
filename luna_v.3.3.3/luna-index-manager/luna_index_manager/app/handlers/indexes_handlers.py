"""
Module realize IndexesHandler for work with indexation tasks.
"""
from tornado import gen

from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import listStringsGetter, statusGetter
from crutches_on_wheels.handlers.query_getters import listUUIDsGetter


class IndexesHandler(BaseRequestHandler):
    """
    Handler for work with indexation tasks
    """

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        """
        Request to get tasks.


        Resource is reached by address '/indexes'

        .. http:get:: /indexes


            :reqheader LUNA-Request-Id: request id

            :query page: page count, default 1
            :query page_size: page size, default 10
            :query generations: coma separated list of generations
            :query list_ids: coma separated list of luna lists
            :query status: status of task


            .. sourcecode:: http

                GET /indexes HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                Content-Type: application/json

            .. json:object:: luna_task_error

                :property iso8601 error_time: error time
                :property string error_massage: string or string which is duped from dict with errors detail

            .. json:object:: luna_index_task

                :property uuid4 list_id: list id
                :property string generation: generation of index from indexer
                :property integer task_id: task id
                :proptype integer status: status of task 0 - success done, 1 - failed, 2 - cancelled
                :property iso8601 start_index_time: start time of the index step
                :property iso8601 end_index_time: end time of the index step
                :property iso8601 start_upload_index_time: start time of the index upload step
                :property iso8601 end_upload_index_time: end time of the index upload  step
                :property iso8601 start_reload_index_time: start time of the index reload step
                :property iso8601 end_reload_index_time: end time of the index reload step
                :property iso8601 start_time: task start time
                :property iso8601 end_time: task end time
                :property iso8601 last_update_time: task last update time
                :property :json:object:`luna_task_error` error: task error

            .. json:object:: luna_index_tasks:
                :showexample:

                :property :json:object:`_list_luna_index_task` tasks: tasks
                :property integer count: task count


            :statuscode 200: Ok
            :statuscode 500: internal server error

        """
        page, pageSize = self.getPagination()
        generations = self.getQueryParam("generations", listStringsGetter)
        lists = self.getQueryParam("list_ids", listUUIDsGetter)
        status = self.getQueryParam("status", statusGetter)
        tasks, count = self.dbContext.searchTasks(page, pageSize, generations, lists, status)
        self.success(outputJson={"tasks": tasks, "count": count})
