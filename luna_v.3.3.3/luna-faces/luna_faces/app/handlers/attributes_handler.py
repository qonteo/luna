from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import timeFilterGetter, uuid4Getter
from crutches_on_wheels.errors.errors import Error


class AttributesHandler(BaseRequestHandler):
    """
    Handler for work with attributes
    """

    @BaseRequestHandler.requestExceptionWrap
    def get(self):
        """
        Resource is reached by address '/attributes'

        .. http:get:: /attributes


            :query page: page count, default 1
            :query page_size: page size, default 10
            :query time__lt: upper bound of attributes last update time
            :query time__gte: lower bound of face create time
            :query list_id: list id
            :query account_id: account id

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                GET /attributes HTTP/1.1

            **Example response**:


                .. sourcecode:: http

                    HTTP/1.1 200 OK
                    Vary: Accept
                    Content-Type: application/json
                    Begin-Request-Time: 1526039272.9173293
                    End-Request-Time: 1526039272.9505265
                    LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295

                .. json:object:: list of attributes
                    :showexample:

                    :property attributes: id of attributes
                    :proptype attributes: _list_(uuid4)
                    :property count: face count
                    :proptype count: integer

            :statuscode 200: Ok
            :statuscode 400: list not found
            :statuscode 500: internal server error
        """
        listId = self.getQueryParam("list_id", uuid4Getter)
        if listId is not None and not self.dbContext.isListExist(listId):
            return self.error(400, error=Error.ListNotFound)

        accountId = self.getQueryParam("account_id", uuid4Getter)

        page, pageSize = self.getPagination(defaultPageSize=1000, maxPageSize=10000)
        createTimeLt = self.getQueryParam("time__lt", timeFilterGetter)
        createTimeGte = self.getQueryParam("time__gte", timeFilterGetter)

        countAttributes, attributes = self.dbContext.getAttributes(listId, accountId, pageSize=pageSize,
                                                                   page=page, updateTimeLt=createTimeLt,
                                                                   updateTimeGte=createTimeGte)
        return self.success(200, outputJson={"count": countAttributes, "attributes": attributes})
