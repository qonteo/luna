import re
from tornado import gen

from app.handlers.base_handler import BaseRequestHandler


def validateBucketName(bucketName: str) -> str:
    """
    Validate bucket name

    Args:
        bucketName: input bucketName

    Returns:
        bucketName
    Raises:
        ValueError: if invalid bucket name
    """
    if bucketName is None:
        raise ValueError
    match = re.match('^[a-z0-9-_]+$', bucketName)
    if match is None:
        raise ValueError
    return bucketName


class BucketsHandler(BaseRequestHandler):
    """
    Handler for work with single bucket or several buckets.
    """

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def post(self):
        """
        .. http:post:: /buckets

            Create new bucket

            :query bucket: new bucket name
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                POST /buckets?bucket=bucketName HTTP/1.1

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 201
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Location: /1/buckets/bucketName/images


            :statuscode 201: Created
            :statuscode 500: Internal server error
        """
        bucketName = self.getQueryParam('bucket', validateBucketName, require=True)

        yield self.storageCtx.createBucket(bucketName)
        self.set_header("Location", "/1/buckets/{}/images".format(bucketName))
        self.success(201)

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        """
        .. http:get:: /buckets

            Get all buckets

            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                GET /buckets HTTP/1.1

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json

                [
                    "53e93231-be6f-4fb6-b2b9-978752db7f92",
                    "d61749a4-0096-4e26-b29d-6ced6c894043"
                ]


            :statuscode 200: Ok
            :statuscode 500: internal server error
        """
        buckets = yield self.storageCtx.getBuckets()
        self.success(200, outputJson=buckets)
