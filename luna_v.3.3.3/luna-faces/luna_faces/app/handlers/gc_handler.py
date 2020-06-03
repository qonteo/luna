from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import timeFilterGetter, uuid4Getter


class GCHandler(BaseRequestHandler):
    """
    Handler removing old descriptors
    """

    @BaseRequestHandler.requestExceptionWrap
    def patch(self):
        """
        Resource is reached by address '/gc'

        .. http:get:: /gc


            :query time__lt: upper bound of free faces update time
            :query account_id: account id
            :query limit: limit

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                PATCH /faces HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295

            .. json:object:: list of removing faces
                :showexample:

                :property attributes: id of removing faces
                :proptype attributes: _list_(uuid4)

            :statuscode 200: Ok
            :statuscode 404: list not found
            :statuscode 500: internal server error
        """

        updateTimeLt = self.getQueryParam("time__lt", timeFilterGetter)
        accountId = self.getQueryParam("account_id", uuid4Getter)
        limit = self.getQueryParam("limit", lambda x: int(x) if (0 < int(x) <= 1000) else 1000, default=1000)
        removingFaces = self.dbContext.removeFreeFaces(limit=limit, accountId=accountId, timeLt=updateTimeLt)
        return self.success(200, outputJson={"face_ids": removingFaces})
