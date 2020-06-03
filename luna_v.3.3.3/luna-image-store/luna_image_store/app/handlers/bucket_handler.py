from typing import Generator

from tornado import gen

from app.handlers.base_handler import BaseRequestHandler


class BucketHandler(BaseRequestHandler):
    """
    Handler for work with single bucket
    """

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def delete(self, bucketName: str):
        """
        .. http:delete:: /buckets/{bucketName}

           Delete bucket from storage

            :param bucketName: bucket name
            :reqheader LUNA-Request-Id: request id

            **Example request**:

            .. sourcecode:: http

                DELETE /buckets/991544fa-c093-40a9-8dd2-b3855f72f507 HTTP/1.1

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 202
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f

            :statuscode 202: Accepted
            :statuscode 500: internal server error
        """
        self.bucket = bucketName
        self.success(202)

    @gen.coroutine
    def on_finish(self) -> Generator:
        """
        On DELETE method - delete bucket after send response in background.
        """
        if self.request.method == 'DELETE':
            yield self.storageCtx.deleteBucket(self.bucket)
