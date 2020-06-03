from luna3.common.exceptions import LunaApiException
from tornado import gen, web

from app.rest_handlers.query_validators import actionGetter, uuid4Getter
from app.rest_handlers.storage_handlers import StorageHandler
from crutches_on_wheels.utils.timer import timer
from crutches_on_wheels.errors.errors import Error, ErrorInfo


class PersonLinkDescriptorHandler(StorageHandler):
    """
    Handler to attach/detach descriptor to person.
    """

    @web.asynchronous
    @StorageHandler.requestExceptionWrap
    @timer
    @gen.coroutine
    def patch(self, person_id):
        """
        Attach/detach descriptor to person.

        .. http:patch:: /storage/persons/{person_id}/linked_descriptors?do=attach&descriptor_id=16fd2706-8baf-433b-82eb-8c7fada847da

            :param person_id: person id

            :optparam do: 'attach' or 'detach'
            :optparam descriptor_id: descriptor id

            **Example request**:

            :reqheader Authorization: basic authorization

            **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            :reqheader LUNA-Request-Id: request id

            **Example response**:

            .. sourcecode:: http

               HTTP/1.1 204
               Vary: Accept
               LUNA-Request-Id: 1516179740,c06887a2


            :statuscode 204: Descriptor is successfully attached/detached


            Error message is returned in format :json:object:`server_error`.

            :statuscode 400: bad query parameters `do`
            :statuscode 400: account list with corresponding type not found
            :statuscode 400: required parameters 'descriptor_id' not found
            :statuscode 400: object in  query is not UUID4, format: 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
            :statuscode 403: person is currently blocked
            :statuscode 404: person is not found
            :statuscode 409: person or descriptor are already in the list
            :statuscode 500: internal server error
        """

        action = self.getQueryParam('do', actionGetter, require=True)
        photoId = self.getQueryParam('descriptor_id', uuid4Getter, require=True)

        try:
            yield self.luna3Client.lunaFaces.linkFaceToPerson(accountId=self.accountId, personId=person_id,
                                                              faceId=photoId, action=action, raiseError=True)
        except LunaApiException as e:
            error = ErrorInfo(e.json["error_code"], e.json["desc"], e.json["detail"])
            if error == Error.PersonNotFound:
                return self.error(404, error)
            elif error == Error.FaceNotFound:
                error = Error.DescriptorNotFound
                return self.error(400, error)
            elif error == Error.FaceAlreadyAttach:
                error = Error.LinkDescriptorAlreadyExist
                return self.error(409, error)
            raise

        self.success(204)

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def get(self, person_id):
        """
        Get all descriptors, linked to person.
        
        .. http:get:: /storage/persons/{person_id}/linked_descriptor
        
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

            :statuscode 200: Descriptor list is received successfully

            .. json:object:: descriptors_lists
               :showexample:

               :property lists: descriptor list
               :proptype lists: _list_(uuid4)

            Error message is returned in format :json:object:`server_error`.

            :statuscode 404: person not found
            :statuscode 500: internal server error
        
        
        :param person_id: 
        """
        response = yield self.luna3Client.lunaFaces.getPerson(accountId=self.accountId, personId=person_id,
                                                              raiseError=True)
        return self.success(200, outputJson={"descriptors": response.json["faces"]})
