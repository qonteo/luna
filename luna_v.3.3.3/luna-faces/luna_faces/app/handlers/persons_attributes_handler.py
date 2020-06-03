from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import listUUIDsGetter, uuid4Getter
from crutches_on_wheels.errors.errors import Error


class PersonAttributesHandler(BaseRequestHandler):
    """
    Handler for work with person attributes
    """
    @BaseRequestHandler.requestExceptionWrap
    def get(self, personId: str):
        """
        Request to get the person attributes id.

        :param personId: person id

        Resource is reached by address '/persons/{personId}'

        .. http:get:: /persons/{personId}/attributes

            :param personId: person id

            :query account_id: account id, this parameter determine, that action must be done with only with objects
                               of this account.

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                GET /persons/{personId}/attributes HTTP/1.1

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                Content-Type: application/json

            Output persons will be represent in :json:object:`luna_person_attributes`.

            :statuscode 200: Ok
            :statuscode 404: person not found
            :statuscode 500: internal server error

        """
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        personAttrs = self.dbContext.getPersonsAttributes([personId], accountId)
        if personAttrs:
            return self.success(200, outputJson=personAttrs[0])
        else:
            return self.error(404, error=Error.PersonNotFound)


class PersonsAttributesHandler(BaseRequestHandler):
    """
    Handler for work with persons attributes
    """
    @BaseRequestHandler.requestExceptionWrap
    def get(self):
        """
        Request to get list of persons attributes id.

        Resource is reached by address '/persons/attributes'

        .. http:get:: /persons/attributes

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id, this parameter determine, that action must be done with only with objects
                               of this account.

            :query persons_ids: coma-separated persons id list.

            .. sourcecode:: http

                GET /persons/attributes HTTP/1.1

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                Content-Type: application/json

            Output persons attributes will be represent in list of :json:object:`luna_person_attributes`.

            :statuscode 200: Ok
            :statuscode 500: internal server error

        """
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        personsIds = self.getQueryParam("persons_ids", listUUIDsGetter, require=True)
        attributesIDs = self.dbContext.getPersonsAttributes(personsIds, accountId)
        return self.success(200, outputJson=attributesIDs)
