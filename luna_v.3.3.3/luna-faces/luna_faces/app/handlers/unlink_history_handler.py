from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import timeFilterGetter


class UnlinkHistoryHandler(BaseRequestHandler):
    """
    Handler for work with unlinking log
    """

    @BaseRequestHandler.requestExceptionWrap
    def patch(self):
        """
        Clean history of unlink attributes from lists. This history is need for correct updating cash in matchers.


        Resource is reached by address '/linker/unlink_history'

        .. http:patch:: /linker/unlink_history

            :query time__lt: upper bound of unlink attributes time


            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                PATCH /linker/log HTTP/1.1

            **Example response**:


                .. sourcecode:: http

                    HTTP/1.1 204 OK
                    Vary: Accept
                    Content-Type: application/json
                    Begin-Request-Time: 1526039272.9173293
                    End-Request-Time: 1526039272.9505265
                    LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295



            :statuscode 204: Ok
            :statuscode 400: list not found
            :statuscode 500: internal server error
        """
        createTimeLt = self.getQueryParam("time__lt", timeFilterGetter)
        self.dbContext.cleanLog(createTimeLt)
        return self.success(204)
