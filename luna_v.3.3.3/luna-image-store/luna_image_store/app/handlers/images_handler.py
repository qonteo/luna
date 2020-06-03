import uuid
from typing import Generator

from tornado import gen

from app.handlers.base_handler import BaseRequestHandler
from app.handlers.helpers import getThumbnails, isCorrectContentType, convertImageToJPG, isCacheable
from configs.config import THUMBNAILS, CACHE_ENABLED
from crutches_on_wheels.errors.errors import Error
from preview.preview_queue import THUMBNAIL_QUEUE


class ImagesHandler(BaseRequestHandler):
    """
    Handler for work with single image or several images.
    """

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def post(self, bucketName: str) -> Generator:
        """
        .. http:post:: /buckets/{bucketName}/images

            Post image to bucket

            :param bucketName: bucket name
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                POST /buckets/fd5a99ad-6ca3-4019-9bb0-910c0044f676/images HTTP/1.1
                Content-Type: image/jpeg

                b'image body ...'

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 201
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json
                Location: /buckets/fd5a99ad-6ca3-4019-9bb0-910c0044f676/images/a2ac3fb1-8dce-4cd8-9fdd-0fd94200b909

            Body will be returned in format :json:object:`create_image_response`.


            :statuscode 201: Created
            :statuscode 400: Bad Request
            :statuscode 500: Internal server error
        """
        contentType = self.request.headers.get("Content-Type", None)
        if not isCorrectContentType(contentType):
            return self.error(400, error=Error.BadContentType)

        createThumbnails = self.getQueryParam("thumbnails", getThumbnails, default=0)

        image = convertImageToJPG(self.request.body)
        if image is None:
            return self.error(400, error=Error.ConvertImageToJPGError)

        imageId = str(uuid.uuid4())
        yield self.storageCtx.saveImage(image, imageId, bucketName)
        if isCacheable(len(self.request.body)):
            self.storageCache.saveBynaryObj(image, imageId, bucketName)

        response = {"image_id": imageId, "url": "/1/buckets/{}/images/{}".format(bucketName, imageId)}

        if createThumbnails:

            for thumbnailSize in THUMBNAILS:
                response["url{}".format(thumbnailSize)] = "/1/buckets/{}/images/{}_{}".format(bucketName, imageId,
                                                                                              thumbnailSize)
            THUMBNAIL_QUEUE.putTask((image, imageId, bucketName, self.logger))

        self.set_header("Location", "/1/buckets/{}/images/{}".format(bucketName, imageId))
        self.success(outputJson=response, statusCode=201)

    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def delete(self, bucketName: str) -> Generator:
        """
        .. http:delete:: /buckets/{bucketName}/images

            Delete images from bucket

            :param bucketName: bucket name
            :reqheader LUNA-Request-Id: request id


            **Example request**:

            .. sourcecode:: http

                DELETE /buckets/fd5a99ad-6ca3-4019-9bb0-910c0044f676/images HTTP/1.1
                Content-Type: application/json

            Body will be represented in format :json:object:`delete_images_response`.

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f


            :statuscode 204: No Content
            :statuscode 400: Bad Request
            :statuscode 500: Internal server error
        """
        reqJson = self.getInputJson()

        if reqJson is None:
            return self.error(400, Error.EmptyJson)

        if not ("images" in reqJson):
            error = Error.formatError(Error.FieldNotInJSON, 'images')
            return self.error(400, error)

        images = reqJson["images"]
        if len(images) > 1000:
            return self.error(400, Error.ImageCountExceededLimit)

        for thumbnail in THUMBNAILS:
            imageForRemoving = ["{}_{}".format(imageId, thumbnail) for imageId in images]
            yield self.storageCtx.deleteImages(imageForRemoving, bucketName)

        if CACHE_ENABLED:
            self.storageCache.deleteBynaryObj(images, bucketName)
        yield self.storageCtx.deleteImages(images, bucketName)

        self.success(204)
