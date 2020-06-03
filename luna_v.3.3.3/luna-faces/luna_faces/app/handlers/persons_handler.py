from app.handlers.base_handler import BaseRequestHandler
from app.handlers.shemas import CREATE_PERSON_SCHEMAS, DELETE_PERSONS_SCHEMA
from app.handlers.query_validators import listUUIDsGetter, uuid4Getter, timeFilterGetter
from app.version import VERSION
from crutches_on_wheels.errors.errors import Error


class PersonsHandler(BaseRequestHandler):
    """
    Faces handler.
    """

    @BaseRequestHandler.requestExceptionWrap
    def post(self):
        """
        Resource is reached by address '/persons'

        .. http:post:: /persons

            Request to create persons.

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                POST /persons HTTP/1.1
                Accept: application/json

            .. json:object:: luna_create_person
                :showexample:

                :property account_id: id of account, required
                :proptype account_id: uuid4
                :property user_data: face information
                :proptype user_data: user_name

            .. sourcecode:: http

                HTTP/1.1 201 Created
                Content-Type: application/json
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Location: /persons/{person_id}

            .. json:object:: person_id
                :showexample:

                :property person_id: id of created person
                :proptype person_id: uuid4

            Error message is returned on format :json:object:`server_error`.

            :statuscode 201: person successfully create
            :statuscode 400: field *user_data* is too large
            :statuscode 400: field *user_data* has wrong type, *string* type is required
            :statuscode 500: internal server error

        """
        data = self.getInputJson()
        self.validateJson(data, CREATE_PERSON_SCHEMAS)
        personId = self.dbContext.createPerson(**data)
        self.add_header("Location", "/{}/persons/{}".format(VERSION["Version"]["api"], personId))
        self.success(201, outputJson={"person_id": personId})

    @BaseRequestHandler.requestExceptionWrap
    def get(self):
        """
        Resource is reached by address '/persons'

        .. http:get:: /persons

            :query page: page count, default 1
            :query page_size: page size, default 10
            :query list_id: list id
            :query account_id: account id
            :query face_ids: list of face ids
            :query face_ids: list of person ids
            :query externalId: external id of the person, if it has its own mapping in external system
            :query user_data: user data
            :query time__lt: upper bound of face create time
            :query time__gte: lower bound of face create time

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

                :property persons: persons
                :proptype faces: _list_(:json:object:`luna_person`)
                :property count: face count
                :proptype count: integer

            :statuscode 200: Ok
            :statuscode 500: internal server error

        """
        page, pageSize = self.getPagination()
        accountId = self.getQueryParam("account_id", uuid4Getter)
        listId = self.getQueryParam("list_id", uuid4Getter)
        personIds = self.getQueryParam("person_ids", listUUIDsGetter)
        faceIds = self.getQueryParam("face_ids", listUUIDsGetter)
        createTimeLt = self.getQueryParam("time__lt", timeFilterGetter)
        createTimeGte = self.getQueryParam("time__gte", timeFilterGetter)
        userData = self.getQueryParam("user_data")
        externalId = self.getQueryParam("external_id")
        personCount, persons = self.dbContext.getPersons(personIds=personIds, createTimeGte=createTimeGte,
                                                         createTimeLt=createTimeLt, accountId=accountId,
                                                         listId=listId, userData=userData, page=page, pageSize=pageSize,
                                                         externalId=externalId, faceIds=faceIds)
        self.success(200, outputJson={"count": personCount, "persons": persons})

    @BaseRequestHandler.requestExceptionWrap
    def delete(self):
        """
        Delete persons

        Resource is reached by address '/persons'

        .. http:delete:: /persons

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                               of this account.


            .. sourcecode:: http

                DELETE /persons/ HTTP/1.1

            .. json:object:: list of persons ids
                :showexample:

                :property person_ids: persons ids
                :proptype person_ids: _list_(uuid4)


            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f



            :statuscode 204: Ok
            :statuscode 400: one or more persons not found
            :statuscode 500: internal server error
        """
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        data = self.getInputJson()
        self.validateJson(data, DELETE_PERSONS_SCHEMA)
        if not self.dbContext.isPersonsExist(data["person_ids"], accountId):
            return self.error(400, error=Error.PersonsNotFound)
        self.dbContext.deletePersons(data["person_ids"])
        self.success(204)
