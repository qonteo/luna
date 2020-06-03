from typing import Optional

from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import uuid4Getter
from app.handlers.shemas import LINK_FACE_TO_PERSON_SCHEMA
from crutches_on_wheels.errors.errors import Error
from db.context import NotUpdatedError


class FaceToPersonLinkerHandler(BaseRequestHandler):
    """
    Handler for attach or detach face from person.
    """

    def investigateFail(self, action: str, faceId: str, personId: str, accountId: Optional[str] = None) -> None:
        """
        Investigate update fail.

        Args:
            action: action, one of: "attach" or "detach"
            faceId: face id
            personId: person id to attach to face
            accountId: face and person account id
        """
        if not self.dbContext.isPersonsExist([personId], accountId):
            return self.error(400, error=Error.PersonNotFound)
        faceIdPersonId = self.dbContext.getPersonIdByFaceId(faceId=faceId, accountId=accountId)
        if faceIdPersonId is None:
            return self.error(400, error=Error.FaceNotFound)
        dbPersonId = faceIdPersonId[1]
        if action == "attach" and dbPersonId is not None:
            return self.error(409, error=Error.FaceAlreadyAttach)
        if action == 'detach' and dbPersonId != personId:
            return self.error(400, error=Error.FaceWasNotAttachedToPerson)
        return self.success(204)

    @BaseRequestHandler.requestExceptionWrap
    def patch(self):
        """
        Link or unlink face to/from person

        Resource is reached by address '/facelinker'

        .. http:patch:: /facelinker

            :reqheader LUNA-Request-Id: request id
            :reqheader Content-Type: application/json

            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                               of this account.

            .. sourcecode:: http

                PATCH /linker HTTP/1.1

            .. json:object:: luna_face_linker
                :showexample:

                :property action:  attach faces to list or detach
                :proptype action: attach or detach
                :property face_id: face id
                :proptype face_id: uuid4
                :property  person_id: person id
                :proptype person_id: uuid4

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f

            :statuscode 204: Ok
            :statuscode 400: face not found
            :statuscode 400: person not found
            :statuscode 409: face already attached
            :statuscode 500: internal server error
        """
        data = self.getInputJson()
        self.validateJson(data, LINK_FACE_TO_PERSON_SCHEMA)
        action = data["action"]
        personId = data["person_id"]
        faceId = data["face_id"]
        accountId = self.getQueryParam("account_id", uuid4Getter)

        try:
            if action == "attach":
                self.dbContext.linkFaceToPerson(personId, faceId, accountId)
            else:
                self.dbContext.unlinkFaceFromPerson(personId, faceId, accountId)
        except NotUpdatedError:
            return self.investigateFail(action, faceId, personId, accountId)
        else:
            return self.success(204)
