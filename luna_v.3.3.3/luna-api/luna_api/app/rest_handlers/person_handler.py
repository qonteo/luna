from tornado import gen

from app.rest_handlers.storage_handlers import StorageHandler
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from app.functions import convertDateTime


class PersonHandler(StorageHandler):
    """
    Handler to operate with existing person. First you have to authorize and account must be active.
    """

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def get(self, person_id):
        """
        Resource to get person data
        .. http:get:: /storage/persons/{person_id}
        
            :param person_id: person id

            **Example request**:

            :reqheader Authorization: basic authorization

            **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            :reqheader LUNA-Request-Id: request id

            **Example response**:

            .. sourcecode:: http

               HTTP/1.1 200 Ok
               Vary: Accept
               Content-Type: application/json
               LUNA-Request-Id: 1516179740,c06887a2

            Data is returned in format :json:object:`user_data`.

            Message error is returned in format :json:object:`server_error`.
            
            :statuscode 404: person is not found
            :statuscode 500: internal server error

        """
        try:
            response = yield self.luna3Client.lunaFaces.getPerson(accountId=self.accountId, personId=person_id,
                                                                  raiseError=True)
            person = {"id": response.json["person_id"], "create_time": convertDateTime(response.json["create_time"]),
                      "lists": response.json["lists"], "descriptors": response.json["faces"],
                      "user_data": response.json["user_data"], "external_id": response.json["external_id"]}
            return self.success(200, outputJson=person)
        except VLException as e:
            if e.error == Error.PersonNotFound:
                e.statusCode = 404
                e.isCriticalError = False
                raise e

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def patch(self, person_id):
        """
        Resource to change user data of person.
        .. http:patch:: /storage/persons/{person_id}
        
            :param person_id: person id

            **Example request**:

            :reqheader Authorization: basic authorization

            **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                POST /storage/persons/{id} HTTP/1.1
                Accept: application/json            
            
            New user data has to be attached in format :json:object:`user_data`.

            **Example response**:

            .. sourcecode:: http

               HTTP/1.1 204
               LUNA-Request-Id: 1516179740,c06887a2


            :statuscode 204: data successfully update

            Error message is returned in format :json:object:`server_error`.
            
            :statuscode 400: field *user_data* is too large
            :statuscode 400: field *user_data* has wrong type, *string* type is required
            :statuscode 400: field *external_id* is too large
            :statuscode 400: field *external_id* has wrong type, *string* type is required
            :statuscode 404: person not found
            :statuscode 500: internal server error
        """

        info = self.getInfoFromRequest("user_data", default=None)
        externalId = self.getInfoFromRequest("external_id", default=None)

        if type(info) != str and info is not None:
            error = Error.formatError(Error.BadTypeOfFieldInJSON, 'user_data', 'string')
            return self.error(400, error)
        if externalId is not None and type(externalId) != str:
            return self.error(400, Error.BadTypeOfFieldInJSON.errorCode,
                              Error.BadTypeOfFieldInJSON.description.format('external_id', 'string'))
        if externalId is not None and type(externalId) != str:
            return self.error(400, Error.BadTypeOfFieldInJSON.errorCode,
                              Error.BadTypeOfFieldInJSON.description.format('external_id', 'string'))
        if info is not None and len(info) > 128:
            return self.error(400, Error.BigUserData)
        if externalId is not None and len(externalId) > 36:
            return self.error(400, Error.BigExternalId.errorCode, Error.BigExternalId.description)
        if externalId is not None and len(externalId) > 128:
            return self.error(400, Error.BigExternalId.errorCode, Error.BigExternalId.description)

        yield self.luna3Client.lunaFaces.updatePerson(accountId=self.accountId, personId=person_id,
                                                      userData=info, externalId=externalId, raiseError=True)
        self.success(204)

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def delete(self, person_id):
        """
            Resource for person deletion.
            
            Person and all its lists will be blocked for deletion/objects addition during person deletion.
            After deletion, all objects must be unblocked (regardless, deletion was successful or not).
                        
            .. http:patch:: /storage/persons/{person_id}

                :param person_id: person id

                **Example request**:

                :reqheader Authorization: basic authorization

                **or**

                :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'


                **Example response**:

                .. sourcecode:: http

                   HTTP/1.1 204 Ok
                   Vary: Accept
                   LUNA-Request-Id: 1516179740,c06887a2

                :statuscode 204: person is deleted successfully

                Error message is returned in format :json:object:`server_error`.

                :statuscode 404: person not found
                :statuscode 403: person is currently blocked
                :statuscode 500: internal server error
                
        
        """
        yield self.luna3Client.lunaFaces.deletePerson(accountId=self.accountId, personId=person_id,
                                                      raiseError=True)
        self.success(204)
