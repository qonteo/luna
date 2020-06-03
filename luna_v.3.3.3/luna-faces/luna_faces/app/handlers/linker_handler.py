from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import uuid4Getter
from app.handlers.shemas import UPDATE_LIST_SCHEMA
from crutches_on_wheels.errors.errors import Error


class LinkerHandler(BaseRequestHandler):
    """
    Handler for work with list
    """

    @BaseRequestHandler.requestExceptionWrap
    def patch(self):
        """
        Link or unlink face to/from list

        Resource is reached by address '/linker'

        .. http:patch:: /linker

            :reqheader LUNA-Request-Id: request id
            :reqheader Content-Type: application/json

            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                               of this account.

            .. sourcecode:: http

                PATCH /linker HTTP/1.1

            .. json:object:: luna_linker
                :showexample:

                :property action:  attach faces to list or detach
                :proptype action: attach or detach
                :property face_ids: face ids
                :proptype face_ids: _list_uuid4
                :property  list_id: list id
                :proptype list_id: uuid4

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f

            :statuscode 204: Ok
            :statuscode 400: list not found
            :statuscode 400: one or more faces not found
            :statuscode 500: internal server error
        """
        data = self.getInputJson()
        self.validateJson(data, UPDATE_LIST_SCHEMA)
        listId = data["list_id"]
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        if not self.dbContext.isListExist(listId, accountId):
            return self.error(400, error=Error.ListNotFound)
        if "face_ids" in data:
            if not self.dbContext.isFacesExist(data["face_ids"], accountId):
                return self.error(400, error=Error.FacesNotFound)
            if data["action"] == "attach":
                self.dbContext.linkFacesToList(data["list_id"], data["face_ids"])
            else:
                self.dbContext.unlinkFacesFromList(data["list_id"], data["face_ids"])
        else:
            if not self.dbContext.isPersonsExist(data["person_ids"], accountId):
                return self.error(400, error=Error.PersonsNotFound)
            if data["action"] == "attach":
                self.dbContext.linkPersonsToList(data["list_id"], data["person_ids"])
            else:
                self.dbContext.unlinkPersonsFromList(data["list_id"], data["person_ids"])
        self.success(204)
