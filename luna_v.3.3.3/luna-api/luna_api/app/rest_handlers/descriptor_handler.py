from tornado import gen
from app.rest_handlers.storage_handlers import StorageHandler
from app.functions import convertDateTime


class DescriptorHandler(StorageHandler):
    """
    Handler to get information about an existing descriptor. To work with this handler you have to log in and account \
    must be active.
    """

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def get(self, descriptor_id):
        """
        Resource to get descriptor data
        
        .. http:get:: /storage/descriptors/{descriptor_id}
        
            :param descriptor_id: descriptor id
            
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
    
            :statuscode 200: Information about person is received successfully
            
            .. json:object:: descriptor information
               :showexample:

               :property id: descriptor id
               :proptype id: :json:object:`descriptor`

            Error message is given in :json:object:`server_error` format

            :statuscode 404: descriptor not found
            :statuscode 500: internal server error

        """
        response = yield self.luna3Client.lunaFaces.getFace(accountId = self.accountId, faceId = descriptor_id,
                                                            raiseError = True)
        descriptor = {"id": response.json["attributes_id"],
                      "last_update": convertDateTime(response.json["create_time"]),
                      "person_id": response.json["person_id"], "lists": response.json["lists"]}
        return self.success(200, outputJson=descriptor)
