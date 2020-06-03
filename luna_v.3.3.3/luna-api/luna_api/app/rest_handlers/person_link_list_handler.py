from luna3.common.exceptions import LunaApiException
from tornado import gen

from app.rest_handlers.query_validators import actionGetter, uuid4Getter
from app.rest_handlers.storage_handlers import StorageHandler
from crutches_on_wheels.errors.errors import Error, ErrorInfo


class PersonLinkListHandler(StorageHandler):
    """
    Handler to attach person to the list.
    """

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def patch(self, person_id):
        """
        Attach/detach person to account list.

        .. http:patch:: /storage/persons/{person_id}/linked_lists?do=attach&list_id=16fd2706-8baf-433b-82eb-8c7fada847da

            :param person_id: person id

            :optparam do: 'attach' or 'detach'
            :optparam list_id: list id

            **Example request**:

            :reqheader Authorization: basic authorization

            **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            :reqheader LUNA-Request-Id: request id

            **Example response**:

            .. sourcecode:: http

               HTTP/1.1 204
               LUNA-Request-Id: 1516179740,c06887a2



            :statuscode 204: Person is attached/detached successfully


            Error message is returned in format :json:object:`server_error`.

            :statuscode 400: list not found
            :statuscode 400: bad query parameters `do`
            :statuscode 400: account list with corresponding type not found
            :statuscode 400: object in  query is not UUID4, format: 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
            :statuscode 403: list or person is blocked
            :statuscode 404: person not found
            :statuscode 409: person or descriptor is already in list
            :statuscode 500: internal server error
        """
        action = self.getQueryParam('do', actionGetter, require=True)
        listId = self.getQueryParam('list_id', uuid4Getter, require=True)

        try:
            yield self.luna3Client.lunaFaces.link(listId, accountId=self.accountId, personIds=[person_id],
                                                  action=action, raiseError=True)
        except LunaApiException as e:
            error = ErrorInfo(e.json["error_code"], e.json["detail"], e.json["detail"])
            if error == Error.PersonsNotFound:
                error = Error.PersonNotFound
                return self.error(404, error)
            raise

        self.success(204)

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def get(self, person_id):
        """
        Get all account lists, person is linked to.

        .. http:get:: /storage/descriptors/{person_id}/linked_lists

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

            .. json:object:: persons_lists
               :showexample:

               :property lists: All lists
               :proptype lists: _list_(uuid4)

            Error message is returned in format :json:object:`server_error`.

            :statuscode 200: Lists are received successfully
            :statuscode 404: person not found
            :statuscode 500: internal server error
        """
        response = yield self.luna3Client.lunaFaces.getPerson(accountId=self.accountId, personId=person_id,
                                                              raiseError=True)
        self.success(200, outputJson={"lists": response.json["lists"]})
