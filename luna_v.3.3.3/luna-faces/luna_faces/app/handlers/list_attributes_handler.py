from app.handlers.base_handler import BaseRequestHandler
from crutches_on_wheels.errors.errors import Error


class ListDescriptorsHandler(BaseRequestHandler):
    """
    Handler for work with attributes of list
    """

    @BaseRequestHandler.requestExceptionWrap
    def get(self, listId: str):
        """
        Resource is reached by address '/lists/{listId}/attributes'

        .. http:get:: /lists/{listId}/attributes

            :param listId: list id

            :query link_key__lt: upper bound of a link key
            :query link_key__gte: lower bound of a link key
            :query list_id: list id
            :query limit: limit

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                GET  /lists/{listId}/attributes HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295


            .. json:object:: plus_delta
                :showexample:

                :property uuid4 attributes_id: attributes id
                :property integer link_key: link key

            Returns list of :json:object:`plus_delta`


            :statuscode 200: Ok
            :statuscode 404: list not found
            :statuscode 500: internal server error
        """
        if not self.dbContext.isListExist(listId):
            return self.error(404, error=Error.ListNotFound)

        linkKeyLt = self.getQueryParam("link_key__lt", lambda x: int(x))
        linkKeyGte = self.getQueryParam("link_key__gte", lambda x: int(x))
        limit = self.getQueryParam("limit", lambda x: int(x), default=1000)

        attributes = self.dbContext.getListPlusDelta(listId, linkKeyLt=linkKeyLt, linkKeyGte=linkKeyGte,
                                                     limit=limit)
        return self.success(200, outputJson=attributes)


class ListDeletionsHandler(BaseRequestHandler):
    """
    Handler for work with deletions history of list
    """

    @BaseRequestHandler.requestExceptionWrap
    def get(self, listId: str):
        """
        Get deletions history.

        Resource is reached by address '/lists/{listId}/deletions'

        .. http:get:: /lists/{listId}/deletions

            :param listId: list id

            :query unlink_key__lt: upper bound of attributes create time
            :query unlink_key__gte: lower bound of face create time
            :query list_id: list id
            :query limit: limit

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                GET /lists/{listId}/deletions HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295

            .. json:object:: minus_delta
                :showexample:

                :property uuid4 attributes_id: attributes id
                :property integer link_key: link key
                :property integer unlink_key: unlink_key

            Returns list of :json:object:`minus_delta`


            :statuscode 200: Ok
            :statuscode 404: list not found
            :statuscode 500: internal server error
        """
        if not self.dbContext.isListExist(listId):
            return self.error(404, error=Error.ListNotFound)

        unlinkKeyLt = self.getQueryParam("unlink_key__lt", lambda x: int(x))
        unlinkKeyGte = self.getQueryParam("unlink_key__gte", lambda x: int(x))
        limit = self.getQueryParam("limit", lambda x: int(x), default=1000)

        attributes = self.dbContext.getListMinusDelta(listId, unlinkKeyLt=unlinkKeyLt, unlinkKeyGte=unlinkKeyGte,
                                                      limit=limit)
        return self.success(200, outputJson=attributes)
