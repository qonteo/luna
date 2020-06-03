"""
Module realize IndexesHandler for work with indexation tasks.
"""
from luna3.common.exceptions import LunaApiException
from tornado import gen

from app.global_workers import crawler
from app.handlers.base_handler import BaseRequestHandler


class IndexedListHandler(BaseRequestHandler):
    """
    Handler for work with indexation tasks
    """

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        """
        Request to get lists waiting indexing.


        Resource is reached by address '/indexes/lists'

        .. http:get:: /indexes/lists


            :reqheader LUNA-Request-Id: request id


            .. sourcecode:: http

                GET /queue HTTP/1.1

            **Example response**:


                .. sourcecode:: http

                    HTTP/1.1 200
                    LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                    Begin-Request-Time: 1526039272.9173293
                    End-Request-Time: 1526039272.9505265
                    Content-Type: application/json

            .. json:object:: indexed_list:
                :showexample

                :property str generation: generation name
                :property uuid4 list_id: list id

            Output account will be represent in list of :json:object:`indexed_list`.


            :statuscode 200: Ok
            :statuscode 500: internal server error

        """
        if not self.dbContext.isIndexesUploadToMatcher():
            return self.success(outputJson={'lists': []})
        generationsAndLists = self.dbContext.getCurrentGenerations()
        reply = []
        for listId, generation in generationsAndLists.items():
            try:
                status, lunaList = yield crawler.checkIndexationCriterion(listId)
            except LunaApiException as e:
                if e.statusCode == 404:
                    continue
                raise
            else:
                if status:
                    reply.append({"generation": generation, "list_id": listId})
        return self.success(outputJson={'lists': reply})
