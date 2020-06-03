from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import uuid4Getter
from app.handlers.shemas import UPDATE_FACE_SCHEMAS, CREATE_FACE_SCHEMAS
from app.version import VERSION
from crutches_on_wheels.errors.errors import Error


class FaceHandler(BaseRequestHandler):
    """
    Handler for work with face
    """

    @BaseRequestHandler.requestExceptionWrap
    def prepare(self):
        """
        Checking exist face or not.

        If face is not exist, will call self.error with error Error.FaceNotFound
        """
        if self.request.method in ("PUT", "GET"):
            return
        faceId = self.request.uri.split("/")[-1].split("?")[0]
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        if not self.dbContext.isFaceExist(faceId, accountId):
            self.error(404, error=Error.FaceNotFound)

    @BaseRequestHandler.requestExceptionWrap
    def head(self, faceId: str):
        """
        Request to check the face existence.

        :param faceId: face id

        Resource is reached by address '/faces/{faceId}'

        .. http:head:: /faces/{faceId}

            :param faceId: face id

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                               of this account.

            .. sourcecode:: http

                HEAD /faces/{faceId} HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                Content-Type: application/json

            :statuscode 200: Ok
            :statuscode 404: face not found
            :statuscode 500: internal server error

        """
        self.success(200)

    @BaseRequestHandler.requestExceptionWrap
    def get(self, faceId: str):
        """
        Request to get the face.

        :param faceId: face id

        Resource is reached by address '/faces/{faceId}'

        .. http:get:: /faces/{faceId}

            :param faceId: face id

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                               of this account.

            .. sourcecode:: http

                GET /faces/{faceId} HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                Content-Type: application/json

            Output face will be represent in  :json:object:`luna_face`.


            :statuscode 200: Ok
            :statuscode 404: face not found
            :statuscode 500: internal server error

        """
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        count, faces = self.dbContext.getFaces(faceIds=[faceId], accountId=accountId)
        if count:
            return self.success(200, outputJson=faces[0])
        else:
            return self.error(404, error=Error.FaceNotFound)

    @BaseRequestHandler.requestExceptionWrap
    def delete(self, faceId: str):
        """
        Delete face

        Request to remove the face.

        :param faceId: face id

        Resource is reached by address '/faces/{faceId}'

        .. http:delete:: /faces/{faceId}

            :param faceId: face id

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                               of this account.

            .. sourcecode:: http

                DELETE /faces/{faceId} HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f

            :statuscode 204: Ok
            :statuscode 404: face not found
            :statuscode 500: internal server error
        """
        self.dbContext.deleteFaces([faceId])
        return self.success(204)

    @BaseRequestHandler.requestExceptionWrap
    def patch(self, faceId: str):
        """
        Patch face. You could patch following params: attributes_id, event_id, user_data.

        Patch data for the face.

        :param faceId: face id

        Resource is reached by address '/faces/{faceId}'

        .. http:patch:: /faces/{faceId}

            :param faceId: face id

            :reqheader LUNA-Request-Id: request id
            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                                  of this account.

            .. sourcecode:: http

                PATCH /faces/{faceId} HTTP/1.1

                .. json:object:: luna_patch_face
                    :showexample:

                    :property attributes_id:  attributes id
                    :proptype attribute_id: uuid4
                    :property user_data: face information
                    :proptype user_data: user_name
                    :property event_id: reference to event which created face
                    :proptype event_id: uuid4
                    :property external_id: external id of the face, if it has its own mapping in external system
                    :proptype external_id: str

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f

            :statuscode 204: Ok
            :statuscode 404: face not found
            :statuscode 500: internal server error
        """
        data = self.getInputJson()
        self.validateJson(data, UPDATE_FACE_SCHEMAS)
        self.dbContext.updateFace(faceId, **data)
        self.success(204)

    @BaseRequestHandler.requestExceptionWrap
    def put(self, faceId: str):
        """
        Resource is reached by address ' /faces/{faceId}'

        .. http:put::  /faces/{faceId}

            Request to create face.

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                PUT  /faces/{faceId} HTTP/1.1
                Accept: application/json

            .. json:object:: luna_put_face
                :showexample:

                :property account_id: id of account, required
                :proptype account_id: uuid4
                :property attributes_id:  attributes id
                :proptype attributes_id: uuid4
                :property user_data: face information
                :proptype user_data: user_name
                :property event_id: reference to event which created face
                :proptype event_id: uuid4
                :property external_id: external id of the face, if it has its own mapping in external system
                :proptype external_id: str

            .. sourcecode:: http

                HTTP/1.1 200 Ok
                Content-Type: application/json
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Location: /faces/{face_id}

            .. json:object:: face_id
                :showexample:

                :property face_id: id of created face
                :proptype face_id: uuid4

            Error message is returned on format :json:object:`server_error`.

            :statuscode 201: face successfully create
            :statuscode 400: field *user_data* is too large
            :statuscode 400: field *user_data* has wrong type, *string* type is required
            :statuscode 409: face with sane attribute_id already exist
            :statuscode 500: internal server error

        """
        data = self.getInputJson()
        self.validateJson(data, CREATE_FACE_SCHEMAS)
        self.dbContext.createFace(faceId, **data)
        self.add_header("Location", "/{}/faces/{}".format(VERSION["Version"]["api"], faceId))
        self.success(200, outputJson={"face_id": faceId})
