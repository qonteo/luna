from app.handlers.base_handler import BaseRequestHandler
from tornado import gen
from app.handlers.helpers import getThumbnails, isCorrectContentType, convertImageToJPG, isCacheable
from configs.config import THUMBNAILS, CACHE_ENABLED
from crutches_on_wheels.errors.errors import Error
import ujson as json
from preview.preview_queue import THUMBNAIL_QUEUE
from typing import Optional, Generator


class ImageHandler(BaseRequestHandler):
    """
    Handler for work with single image
    """

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def head(self, bucketName: str, imageId: str, thumbnail: Optional[str]):
        """
        .. http:head:: /buckets/{bucketName}/images/{imageId}{thumbnail}

            Check image exists in bucket.

            :param bucketName: bucket name
            :param imageId: image id
            :param thumbnail: thumbnail
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                HEAD /buckets/3a02c949-3f60-4143-90cb-8ea0a25b8d15/images/dbf98a33-6e05-4fb2-ba53-17a2caba4647 HTTP/1.1

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: image/jpeg


            :statuscode 200: Ok
            :statuscode 404: image not found
            :statuscode 500: internal server error
        """
        if thumbnail:
            isImageExists = yield self.storageCtx.checkImage(imageId + thumbnail, bucketName)

        else:
            isImageExists = self.storageCache.checkBynaryObj(imageId, bucketName) if CACHE_ENABLED else None
            if not isImageExists:
                isImageExists = yield self.storageCtx.checkImage(imageId, bucketName)

        if not isImageExists:
            return self.error(404, Error.ImageNotFoundError)

        self.success(200, contentType="image/jpeg")

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def put(self, bucketName: str, imageId: str, thumbnail: Optional[str]):
        """
        .. http:put:: /buckets/{bucketName}/images/{imageId}{thumbnail}

            Put image to bucket

            :param bucketName: bucket name
            :param imageId: image id
            :query thumbnail: thumbnail - create or not
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                PUT /buckets/3a02c949-3f60-4143-90cb-8ea0a25b8d15/images/dbf98a33-6e05-4fb2-ba53-17a2caba4647 HTTP/1.1
                Content-Type: image/jpeg

                b'image body ...'

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json

                {"url": "/1/buckets/3a02c949-3f60-4143-90cb-8ea0a25b8d15/images/dbf98a33-6e05-4fb2-ba53-17a2caba4647"}


            :statuscode 200: Ok
            :statuscode 400: Bad Request
            :statuscode 404: Not Found
            :statuscode 500: internal server error
        """

        if thumbnail is not None:
            return self.error(404, error=Error.PageNotFoundError)
        createThumbnails = self.getQueryParam("thumbnails", getThumbnails, default=0)

        contentType = self.request.headers.get("Content-Type", None)
        if not isCorrectContentType(contentType):
            return self.error(400, error=Error.BadContentType)

        image = convertImageToJPG(self.request.body)
        if image is None:
            return self.error(400, error=Error.ConvertImageToJPGError)

        yield self.storageCtx.saveImage(image, imageId, bucketName)
        if isCacheable(len(self.request.body)):
            self.storageCache.saveBynaryObj(image, imageId, bucketName)

        response = {"url": "/1/buckets/{}/images/{}".format(bucketName, imageId)}
        if createThumbnails:
            THUMBNAIL_QUEUE.putTask((image, imageId, bucketName, self.logger))
            for thumbnailSize in THUMBNAILS:
                response["url{}".format(thumbnailSize)] = "/1/buckets/{}/images/{}_{}".format(bucketName, imageId,
                                                                                              thumbnailSize)
        self.success(outputJson=response, statusCode=200)

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def delete(self, bucketName: str, imageId: str, thumbnail: Optional[str]) -> Generator:
        """
        .. http:delete:: /buckets/{bucketName}/images/{imageId}{thumbnail}

            Delete image from bucket

            :param bucketName: bucket name
            :param imageId: image id
            :param thumbnail: thumbnail - create or not
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                DELETE /buckets/3a02c949-3f60-4143-90cb-8ea0a25b8d15/images/dbf98a33-6e05-4fb2-ba53-17a2caba4647 HTTP/1.1

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f


            :statuscode 204: No content
            :statuscode 500: internal server error
        """
        imageForRemoving = ["{}_{}".format(imageId, thumbnail) for thumbnail in THUMBNAILS]
        imageForRemoving.append(imageId)
        if CACHE_ENABLED:
            self.storageCache.deleteBynaryObj([imageId], bucketName)
        yield self.storageCtx.deleteImages(imageForRemoving, bucketName)
        self.success(204)

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def get(self, bucketName: str, imageId: str, thumbnail: Optional[str]) -> Generator:
        """
        .. http:get:: /buckets/{bucketName}/images/{imageId}{thumbnail}

            Get image from bucket.

            :param bucketName: bucket name
            :param imageId: image id
            :param thumbnail: thumbnail - create or not
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                GET /buckets/3a02c949-3f60-4143-90cb-8ea0a25b8d15/images/dbf98a33-6e05-4fb2-ba53-17a2caba4647 HTTP/1.1

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: image/jpeg

                b'image body ...'


            :statuscode 200: Ok
            :statuscode 500: internal server error
        """
        if thumbnail:
            image = yield self.storageCtx.getImage(imageId + thumbnail, bucketName)

        else:
            image = self.storageCache.getBynaryObj(imageId, bucketName) if CACHE_ENABLED else None
            if not image:
                image = yield self.storageCtx.getImage(imageId, bucketName)

        return self.success(statusCode=200, body=image, contentType="image/jpeg")
