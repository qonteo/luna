from luna3.common.exceptions import LunaApiException
from tornado import gen
from app.rest_handlers.query_validators import actionGetter, uuid4Getter
from app.rest_handlers.storage_handlers import StorageHandler
from crutches_on_wheels.errors.errors import Error, ErrorInfo


class PhotoLinkListHandler(StorageHandler):
    """
    Handler to add or delete descriptors in lists. 
    """

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def patch(self, photo_id):
        """
        Attach/detach descriptor to account list.

        .. http:patch:: /storage/descriptors/{photo_id}/linked_lists?do=attach&list_id=16fd2706-8baf-433b-82eb-8c7fada847da

            :param photo_id: descriptor id
            
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



            :statuscode 204: Descriptor is successfully attached/detached


            Error message is returned in format :json:object:`server_error`.

            :statuscode 400: list not found
            :statuscode 400: Bad query parameters `do`
            :statuscode 400: Account list with corresponding type not found
            :statuscode 400: Object in  query is not UUID4, format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
            :statuscode 403: list or person is blocked
            :statuscode 404: descriptor not found
            :statuscode 409: descriptor is already in list
            :statuscode 500: internal server error
        """
        action = self.getQueryParam('do', actionGetter, require=True)
        listId = self.getQueryParam('list_id', uuid4Getter, require=True)

        try:
            yield self.luna3Client.lunaFaces.link(listId, accountId=self.accountId, faceIds=[photo_id],
                                                  action=action, raiseError=True)
        except LunaApiException as e:
            error = ErrorInfo(e.json["error_code"], e.json["desc"], e.json["detail"])
            if error == Error.FacesNotFound:
                error = Error.DescriptorNotFound
                return self.error(404, error)
            raise

        self.success(204)

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def get(self, photo_id):
        """
        Get all account lists, descriptor is linked to.
        
        .. http:get:: /storage/descriptors/{photo_id}/linked_lists
        
            :param photo_id: descriptor id
            
            **Example request**:

            :reqheader LUNA-Request-Id: request id

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
               
            :statuscode 200: Lists received successfully
            
            .. json:object:: descriptor_lists
               :showexample:

               :property lists: all lists
               :proptype lists: _list_(uuid4)

            Error message is returned in format :json:object:`server_error`.

            :statuscode 404: descriptor not found
            :statuscode 500: internal server error
        """
        response = yield self.luna3Client.lunaFaces.getFace(accountId=self.accountId, faceId=photo_id,
                                                            raiseError=True)
        self.success(200, outputJson={"lists": response.json["lists"]})
