from tornado import gen

from app.handlers.base_handler import BaseRequestHandler
from app.handlers.helpers import isCorrectTextContentType, matchContentType, isJson
from crutches_on_wheels.errors.errors import Error


class ObjectHandler(BaseRequestHandler):
    """
    Handler for work with object(text/json).
    """

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def head(self, bucketName: str, objectId: str) -> None:
        """
        .. http:head:: /buckets/{bucketName}/objects/{objectId}

            Check object exists in bucket

            :param bucketName: bucket name
            :param objectId: object id
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                HEAD /buckets/fd5a99ad-6ca3-4019-9bb0-910c0044f676/objects/a2ac3fb1-8dce-4cd8-9fdd-0fd94200b909 HTTP/1.1
                Content-Type: application/json

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json


            :statuscode 200: Ok
            :statuscode 404: object not found
            :statuscode 406: Not Acceptable
            :statuscode 500: internal server error
        """
        isObjectExists = yield self.storageCtx.checkObject(objectId, bucketName)

        contentType = self.request.headers['Accept'] if 'Accept' in self.request.headers else 'text/plain'

        if not isCorrectTextContentType(contentType):
            return self.error(400, Error.BadContentType)

        if not isObjectExists:
            return self.error(404, Error.ObjectNotFound)

        return self.success(statusCode=200, contentType=contentType)

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def put(self, bucketName: str, objectId: str) -> None:
        """
        .. http:put:: /buckets/{bucketName}/objects/{objectId}

            Put object to bucket

            :param bucketName: bucket name
            :param objectId: object id
            :reqheader LUNA-Request-Id: request id
            :reqheader Content-Type: application/json or text/plain

            **Example request**:

            .. sourcecode:: http

                PUT /buckets/991544fa-c093-40a9-8dd2-b3855f72f507/objects/a2a5df7e-db47-449d-a27c-824405b79074 HTTP/1.1
                Content-Type: application/json

                {"body": "data"}

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json

            Body will be returned on format :json:object:`create_object_response`.


            :statuscode 200: Ok
            :statuscode 400: Bad Request
            :statuscode 415: Unsupported Media Type
            :statuscode 500: internal server error
        """
        contentType = self.request.headers.get("Content-Type", None)
        if not isCorrectTextContentType(contentType):
            return self.error(415, error=Error.UnsupportedMediaType)

        objectBody = self.request.body
        if objectBody is None or objectBody == b'':
            return self.error(400, error=Error.BadBody)

        if not matchContentType(contentType, objectBody):
            return self.error(400, error=Error.SpecifiedTypeNotMatchDataType)

        yield self.storageCtx.saveObject(objectBody, objectId, bucketName)

        response = {'object_id': objectId, 'url': '/1/buckets/{}/objects/{}'.format(bucketName, objectId)}
        self.success(outputJson=response, statusCode=200)

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def get(self, bucketName: str, objectId: str) -> None:
        """
        .. http:get:: /buckets/{bucketName}/objects/{objectId}

            Get object from bucket

            :param bucketName: bucket name
            :param objectId: object id
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                GET /buckets/fd5a99ad-6ca3-4019-9bb0-910c0044f676/objects/a2ac3fb1-8dce-4cd8-9fdd-0fd94200b909 HTTP/1.1
                Content-Type: application/json

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json

                {"body": "data"}


            :statuscode 201: Ok
            :statuscode 400: Bad Request
            :statuscode 406: Not Acceptable
            :statuscode 500: internal server error
        """
        objectBody = yield self.storageCtx.getObject(objectId, bucketName)

        contentType = self.request.headers['Accept'] if 'Accept' in self.request.headers else 'text/plain'

        if not isCorrectTextContentType(contentType):
            return self.error(400, Error.BadContentType)

        if contentType == 'application/json' and not isJson(objectBody):
            return self.error(406, Error.NotAcceptable)

        return self.success(statusCode=200, body=objectBody, contentType=contentType)

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def delete(self, bucketName: str, objectId: str):
        """
        .. http:delete:: /buckets/{bucketName}/objects/{objectId}

            Delete object from bucket

            :param bucketName: bucket name
            :param objectId: object id
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                DELETE /buckets/fd5a99ad-6ca3-4019-9bb0-910c0044f676/objects/a2ac3fb1-8dce-4cd8-9fdd-0fd94200b909 HTTP/1.1

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json


            :statuscode 204: No Content
            :statuscode 500: internal server error
        """
        yield self.storageCtx.deleteObject(objectId, bucketName)
        self.success(204)
