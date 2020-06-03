from tornado import gen
from app.rest_handlers.storage_handlers import StorageHandler
from crutches_on_wheels.errors.errors import Error


class LinkerHandler(StorageHandler):

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def patch(self):
        """
        A request to attach or detach descriptors or persons to list.

        .. http:patch:: /storage/linker

            :reqheader LUNA-Request-Id: request id

            :reqheader Authorization: basic authorization

                **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            .. sourcecode:: http

                PATCH /storage/linker HTTP/1.1
                Content-Type: application/json

            Data has to be attached in one of the following formats:

                .. json:object: multiple_link_request
                    :showexample:

                    :property action: action to perform
                    :proptype action: _enum_(attach)_(detach)
                    :property list_id: list id to link with
                    :proptype list_id: uuid4
                    :property descriptor_ids: descriptor ids to link
                    :proptype descriptor_ids: _list_(uuid4)

                .. json:object: multiple_link_request
                    :showexample:

                    :property action: action to perform
                    :proptype action: _enum_(attach)_(detach)
                    :property list_id: list id to link with
                    :proptype list_id: uuid4
                    :property person_ids: person ids to link
                    :proptype person_ids: _list_(uuid4)

            **Example response**:

            :statuscode 204: objects were linked successfully.

            .. sourcecode:: http

                HTTP/1.1 204 Ok
                LUNA-Request-Id: 1516179740,f1e61acf-cc9d-4b8b-bed9-60ae5417ffc5

            Message error is returned in format :json:object:`server_error`.

            :statuscode 400: list not found
            :statuscode 500: internal server error

        """
        action = self.getInfoFromRequest('action', True)
        listId = self.getInfoFromRequest('list_id', True)
        faceIds = self.getInfoFromRequest('descriptor_ids', default=None)
        personIds = self.getInfoFromRequest('person_ids', default=None)

        reply = yield self.luna3Client.lunaFaces.link(listId, faceIds, personIds, action, self.accountId,
                                                      lunaRequestId=self.requestId, raiseError=True)
        self.success(204)
