from tornado import gen

from app.rest_handlers.storage_handlers import StorageHandler
from crutches_on_wheels.errors.errors import Error
from app.functions import convertDateTime


class PersonCreateHandler(StorageHandler):
    """
    Handler for person creation. To work with this handler you should authorize in the account and it must be active.
    """

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def post(self):
        """
        Request for new account creation

        .. http:post:: /storage/persons

            :reqheader LUNA-Request-Id: request id

            **Example request**:

            :reqheader Authorization: basic authorization

            **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            .. sourcecode:: http

                POST /storage/persons HTTP/1.1
                Accept: application/json
            
            You can attach user data in format :json:object:`user_data` and/or external id in
            format :json:object:`external_id`.

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 201 Created
                Vary: Accept
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2


            .. json:object:: id_person
                :showexample:

                :property person_id: id of created person
                :proptype person_id: uuid4


            Error message is returned on format :json:object:`server_error`.
            
            :statuscode 400: field *user_data* is too large
            :statuscode 400: field *user_data* has wrong type, *string* type is required
            :statuscode 400: field *external_id* is too large
            :statuscode 400: field *external_id* has wrong type, *string* type is required
            :statuscode 500: internal server error
        """

        info = self.getInfoFromRequest("user_data")
        externalId = self.getInfoFromRequest("external_id", default=None)

        if type(info) != str:
            error = Error.formatError(Error.BadTypeOfFieldInJSON, 'user_data', 'string')
            return self.error(400, error)
        if externalId is not None and type(externalId) != str:
            error = Error.formatError(Error.BadTypeOfFieldInJSON, 'external_id', 'string')
            return self.error(400, error)

        if len(info) > 128:
            return self.error(400, Error.BigUserData)
        if externalId is not None and len(externalId) > 128:
            return self.error(400, Error.BigExternalId)

        response = yield self.luna3Client.lunaFaces.createPerson(accountId=self.accountId, userData=info,
                                                                 externalId=externalId, raiseError=True)
        return self.success(201, outputJson=response.json)


    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        """
        Resource to get all persons.
        
        .. http:post:: /storage/persons?page=1&page_size=10
        
            :optparam page: A number of page. Minimum 1, default 1. 
            :optparam page_size: Persons count on page.  Minimum 1, maximum 100, default 10. 
            
            :reqheader LUNA-Request-Id: request id

            **Example request**:

            :reqheader Authorization: basic authorization

            **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            :query user_data: user data or part of user data to search by it

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200 Ok
                Vary: Accept
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2

            :statuscode 200: person ids and number of persons are received successfully 
            
            .. json:object:: persons_json
                :showexample:

                :property persons: person ids list
                :proptype persons: _list_(:json:object:`person`)
                :property count: number of persons
                :proptype count: int

            Error message is returned on format :json:object:`server_error`.
                            
            :statuscode 400: field *page* or *page_size* has wrong format
            :statuscode 500: internal server error

        """
        page, pageSize = self.getPagination()
        externalId = self.getQueryParam("external_id")
        userData = self.getQueryParam('user_data', require=False, default=None)

        response = yield self.luna3Client.lunaFaces.getPersons(userData=userData, accountId=self.accountId, page=page,
                                                            pageSize=pageSize, externalId=externalId, raiseError=True)
        persons = [{"id": person["person_id"], "create_time": convertDateTime(person["create_time"]),
                    "lists": person["lists"], "descriptors": person["faces"], "user_data": person["user_data"],
                    'external_id': person['external_id']} for person in response.json["persons"]]
        self.success(200, outputJson={"persons": persons, "count": response.json["count"]})
