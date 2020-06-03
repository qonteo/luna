from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import listUUIDsGetter, uuid4Getter
from crutches_on_wheels.errors.errors import Error


class FaceAttributesHandler(BaseRequestHandler):
    """
    Handler for work with face attributes
    """

    @BaseRequestHandler.requestExceptionWrap
    def get(self, faceId: str):
        """
        Request to get the face attributes id.

        :param faceId: face id

        Resource is reached by address '/faces/{faceId}/attributes'

        .. http:get:: /faces/{faceId}/attributes

            :param faceId: face id
            :query account_id: account id, this parameter determine, that action must be done with only with objects
                               of this account.

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                GET /faces/{faceId}/attributes HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                Content-Type: application/json

            Output face will be represent in :json:object:`luna_face_attributes`.

            :statuscode 200: Ok
            :statuscode 404: face not found
            :statuscode 500: internal server error

        """
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        attributes = self.dbContext.getFacesAttributes([faceId], accountId)
        if attributes is None:
            return self.error(404, error=Error.FaceNotFound)
        else:
            return self.success(200, outputJson=attributes[0])


class FacesAttributesHandler(BaseRequestHandler):
    """
    Handler for work with faces attributes
    """

    @BaseRequestHandler.requestExceptionWrap
    def get(self):
        """
        Request to get list of faces attributes id.

        Resource is reached by address '/faces/attributes'

        .. http:get:: /faces/attributes

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id, this parameter determine, that action must be done with only with objects
                               of this account.

            :query faces_ids: coma-separated face id list.

            .. sourcecode:: http

                GET /faces/attributes HTTP/1.1

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                Content-Type: application/json

            Output face will be represent in list of :json:object:`luna_face_attributes`.

            :statuscode 200: Ok
            :statuscode 500: internal server error

        """
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        facesIds = self.getQueryParam("faces_ids", listUUIDsGetter, require=True)

        attributesIDs = self.dbContext.getFacesAttributes(facesIds, accountId)
        return self.success(200, outputJson=attributesIDs or [])
