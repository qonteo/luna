from app.handlers.base_handler import BaseRequestHandler
from tornado import gen
from app.handlers.helpers import isCorrectTextContentType, isJson
from crutches_on_wheels.errors.errors import Error
from uuid import uuid4
from tornado import escape


class ObjectsHandler(BaseRequestHandler):
    """
    Handler for work with signel object or several objects.
    """

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def post(self, bucketName):
        """
        .. http:post:: /buckets/{bucketName}/objects

            Post object to bucket

            :param bucketName: bucket name
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                POST /buckets/fd5a99ad-6ca3-4019-9bb0-910c0044f676/objects HTTP/1.1
                Content-Type: application/json

                {"data": "data"}

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 201
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json
                Location: /buckets/fd5a99ad-6ca3-4019-9bb0-910c0044f676/objects/a2ac3fb1-8dce-4cd8-9fdd-0fd94200b909

            Body will be returned in format :json:object:`create_object_response`.


            :statuscode 201: Created
            :statuscode 400: Bad Request
            :statuscode 415: Unsupported Media Type
            :statuscode 500: Internal server error
        """
        contentType = self.request.headers.get("Content-Type", None)
        if not isCorrectTextContentType(contentType):
            return self.error(415, error=Error.UnsupportedMediaType)

        objectBody = self.request.body
        if objectBody is None or objectBody == b'':
            return self.error(400, error=Error.BadBody)

        if contentType == 'application/json' and not isJson(objectBody):
            return self.error(400, error=Error.SpecifiedTypeNotMatchDataType)

        objectId = str(uuid4())
        yield self.storageCtx.saveObject(objectBody, objectId, bucketName)

        response = {'object_id': objectId, 'url': '/1/buckets/{}/objects/{}'.format(bucketName, objectId)}
        self.set_header("Location", "/1/buckets/{}/objects/{}".format(bucketName, objectId))
        self.success(statusCode=201, outputJson=response)

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def delete(self, bucketName):
        """
        .. http:delete:: /buckets/{bucketName}/objects

            Delete objects from bucket

            :param bucketName: bucket name
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                DELETE /buckets/fd5a99ad-6ca3-4019-9bb0-910c0044f676/objects HTTP/1.1
                Content-Type: application/json

            Body will be represented in format :json:object:`delete_objects_response`.

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f


            :statuscode 204: No Content
            :statuscode 400: Bad Request
            :statuscode 500: Internal server error
        """
        requestJson = self.request.body
        try:
            requestJson = escape.json_decode(requestJson)
        except Exception:
            return self.error(400, Error.RequestNotContainsJson)

        if not ("objects" in requestJson):
            error = Error.formatError(Error.FieldNotInJSON, 'objects')
            return self.error(400, error)

        objectIds = requestJson["objects"]
        if len(objectIds) > 1000:
            return self.error(400, Error.ObjectInBucketCountExceededLimit)

        yield self.storageCtx.deleteObjects(objectIds, bucketName)
        self.success(204)
