from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import uuid4Getter
from app.handlers.shemas import UPDATE_PERSON_SCHEMA
from crutches_on_wheels.errors.errors import Error


class PersonHandler(BaseRequestHandler):
    """
    Handler for work with face
    """

    @BaseRequestHandler.requestExceptionWrap
    def prepare(self):
        """
        Check whether face exists.

        If face does not exist, self.error with error Error.FaceNotFound will be called.
        """
        if self.request.method == "GET":
            return
        personId = self.request.uri.split("/")[-1].split("?")[0]
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        if not self.dbContext.isPersonsExist([personId], accountId):
            self.error(404, error=Error.PersonNotFound)

    @BaseRequestHandler.requestExceptionWrap
    def head(self, personId: str):
        """
        Request to check the face existence.

        :param personId: face id

        Resource is reached by address '/persons/{personId}'

        .. http:get:: /persons/{personId}

             :param personId: person id

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id, this parameter determine, that action must be done with only with objects
                               of this account.

            .. sourcecode:: http

                HEAD /persons/{personId} HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json

            :statuscode 200: Ok
            :statuscode 404: person not found
            :statuscode 500: internal server error

        """
        return self.success(200)

    @BaseRequestHandler.requestExceptionWrap
    def get(self, personId: str):
        """
        Request to get the person.

        :param personId: person id

        Resource is reached by address '/persons/{personId}'

        .. http:get:: /persons/{personId}

            :param personId: person id

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id, this parameter determine, that action must be done with only with objects
                               of this account.

            .. sourcecode:: http

                GET /persons/{personId} HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json

            Output face will be represented in :json:object:`luna_person`.


            :statuscode 200: Ok
            :statuscode 404: person not found
            :statuscode 500: internal server error

        """
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        count, persons = self.dbContext.getPersons(personIds=[personId], accountId=accountId)
        if count:
            return self.success(200, outputJson=persons[0])
        else:
            return self.error(404, error=Error.PersonNotFound)

    @BaseRequestHandler.requestExceptionWrap
    def delete(self, personId: str):
        """
        Delete face

        Request to remove the face.

        :param personId: person id

        Resource is reached by address '/persons/{personId}'

        .. http:delete:: /persons/{personId}

            :param personId: person id

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                               of this account.

            .. sourcecode:: http

                DELETE /persons/{personId} HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f

            :statuscode 204: Ok
            :statuscode 404: person not found
            :statuscode 500: internal server error
        """
        self.dbContext.deletePersons([personId])
        return self.success(204)

    @BaseRequestHandler.requestExceptionWrap
    def patch(self, personId: str):
        """
        Patch face. You could patch following params: user_data, external_id.

        Patch user data of the person.

        :param personId: person id

        Resource is reached by address '/persons/{personId}'

        .. http:patch:: /persons/{personId}

            :param personId: person id

            :reqheader LUNA-Request-Id: request id
            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                                  of this account.

            .. sourcecode:: http

                PATCH /persons/{personId} HTTP/1.1

                .. json:object:: luna_patch_person
                    :showexample:

                    :property user_data: person information
                    :proptype user_data: user_name
                    :property external_id: external id of the person, if it has its own mapping in external system
                    :proptype external_id: uuid4


            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f

            :statuscode 204: Ok
            :statuscode 404: person not found
            :statuscode 500: internal server error
        """
        data = self.getInputJson()
        self.validateJson(data, UPDATE_PERSON_SCHEMA)
        self.dbContext.updatePerson(personId, **data)
        self.success(204)
