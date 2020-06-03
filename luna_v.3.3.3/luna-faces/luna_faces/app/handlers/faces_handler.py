from app.version import VERSION
from app.handlers.base_handler import BaseRequestHandler
from app.handlers.shemas import CREATE_FACE_SCHEMAS, DELETE_FACES_SCHEMA
from app.handlers.query_validators import listUUIDsGetter, uuid4Getter, timeFilterGetter
from crutches_on_wheels.errors.errors import Error


class FacesHandler(BaseRequestHandler):
    """
    Faces handler.
    """

    @BaseRequestHandler.requestExceptionWrap
    def post(self):
        """
        Resource is reached by address '/faces'

        .. http:post:: /faces

            Request to create face.

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                POST /faces HTTP/1.1
                Accept: application/json

            .. json:object:: luna_create_face
                :showexample:

                :property account_id: id of account, required
                :proptype account_id: uuid4
                :property attributes_id:  attributes id
                :proptype attributes_id: uuid4
                :property user_data: face information
                :proptype user_data: user_name
                :property event_id: reference to event which created face
                :proptype event_id: uuid4
                :property externalId: external id of the face, if it has its own mapping in external system
                :proptype externalId: str

            .. sourcecode:: http

                HTTP/1.1 201 Created
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
        faceId = self.dbContext.createFace(**data)
        self.add_header("Location", "/{}/faces/{}".format(VERSION["Version"]["api"], faceId))
        self.success(201, outputJson={"face_id": faceId})

    @BaseRequestHandler.requestExceptionWrap
    def get(self):
        """
        Resource is reached by address '/faces'

        .. http:get:: /faces

            :query page: page count, default 1
            :query page_size: page size, default 10
            :query user_data: user data
            :query time__lt: upper bound of face create time
            :query time__gte: lower bound of face create time
            :query event_id: event id
            :query list_id: list id
            :query account_id: account id
            :query face_ids: list of face ids
            :query externalId: external id of the face, if it has its own mapping in external system

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                GET /faces HTTP/1.1

            **Example response**:



            .. sourcecode:: http

                HTTP/1.1 200 OK
                Vary: Accept
                Content-Type: application/json
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295

            .. json:object:: list of faces
                :showexample:

                :property faces: faces
                :proptype faces: _list_(:json:object:`luna_face`)
                :property count: face count
                :proptype count: integer

            :statuscode 200: Ok
            :statuscode 500: internal server error

        """
        page, pageSize = self.getPagination()
        accountId = self.getQueryParam("account_id", uuid4Getter)
        userData = self.getQueryParam("user_data")
        eventId = self.getQueryParam("event_id", uuid4Getter)
        listId = self.getQueryParam("list_id", uuid4Getter)
        faceIds = self.getQueryParam("face_ids", listUUIDsGetter)
        createTimeLt = self.getQueryParam("time__lt", timeFilterGetter)
        createTimeGte = self.getQueryParam("time__gte", timeFilterGetter)
        externalId = self.getQueryParam("external_id")
        faceCount, faces = self.dbContext.getFaces(eventId=eventId, faceIds=faceIds, userData=userData,
                                                   createTimeGte=createTimeGte, createTimeLt=createTimeLt,
                                                   accountId=accountId, listId=listId,
                                                   page=page, pageSize=pageSize, externalId=externalId)
        self.success(200, outputJson={"count": faceCount, "faces": faces})

    @BaseRequestHandler.requestExceptionWrap
    def delete(self):
        """
        Delete faces

        Resource is reached by address '/faces'

        .. http:delete:: /faces

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                               of this account.


            .. sourcecode:: http

                DELETE /faces/ HTTP/1.1

            .. json:object:: list of faces ids
                :showexample:

                :property face_ids: faces ids
                :proptype face_ids: _list_(uuid4)


            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f



            :statuscode 204: Ok
            :statuscode 400: one or more faces not found
            :statuscode 500: internal server error
        """
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        data = self.getInputJson()
        self.validateJson(data, DELETE_FACES_SCHEMA)
        if not self.dbContext.isFacesExist(data["face_ids"], accountId):
            return self.error(400, error=Error.FacesNotFound)
        self.dbContext.deleteFaces(data["face_ids"])
        self.success(204)
