"""
Module realize QueueHandler for work with waiting indexation lists queue.
"""
from luna3.common.exceptions import LunaApiException
from tornado import gen

from app.global_workers import crawler
from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import actionValidator, QueueActions
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.handlers.query_getters import uuid4Getter


class QueueHandler(BaseRequestHandler):
    """
    Handler for work with waiting indexation lists.
    """

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        """
        Request to get lists waiting indexing.


        Resource is reached by address '/queue'

        .. http:get:: /queue


            :reqheader LUNA-Request-Id: request id

            :query page: page count, default 1
            :query page_size: page size, default 10

            .. sourcecode:: http

                GET /queue HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                Content-Type: application/json

            Output face will be represent in  :json:object:`luna_face`.


            :statuscode 200: Ok
            :statuscode 500: internal server error

        """
        page, pageSize = self.getPagination()
        lists = crawler.buffer[(page - 1) * pageSize: page * pageSize]
        count = len(crawler.buffer.listsForIndexing)
        self.success(outputJson={"lists": [list_.asDict for list_ in lists], "count": count})

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def patch(self):
        """
        The resource enables to clean the indexation queue or  forward list to the head of the queue.

        Resource is reached by address '/queue'

        .. http:patch:: /queue


            :reqheader LUNA-Request-Id: request id

            :query action: forward a list to the head of the queue or clean the queue.
            :query list_id: list id from luna-faces (for action "forward"). This list must satisfy criterion
                            of indexation.

            .. sourcecode:: http

                PATCH /queue HTTP/1.1


            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f

            :statuscode 204: Ok
            :statuscode 400: list not found
            :statuscode 403: List does not satisfy to the indexation condition
            :statuscode 500: internal server error
        """
        action = self.getQueryParam("action", actionValidator, require=True)

        if action == QueueActions.FORWARD.value:
            listId = self.getQueryParam("list_id", uuid4Getter, require=True)
            try:
                checkRes, lunaList = yield crawler.checkIndexationCriterion(listId)
                if checkRes:
                    crawler.buffer.forwardList(lunaList)
                else:
                    return self.error(403, error=Error.ListNotSatisfyIndexationCondition)
                self.success(204)
            except LunaApiException as e:
                if e.statusCode == 404:
                    e.statusCode = 400
                    raise e
                raise

        else:
            crawler.buffer.clear()
            self.success(204)
