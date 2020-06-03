from tests.base_class import BaseClass, createPayloadImg
from tests.resource import STANDARD_IMAGE, IMAGE_NON_STANDARD_FORMATS, NON_IMAGE
from luna_image_store.crutches_on_wheels.errors.errors import Error
import time
from uuid import uuid4


class TestImage(BaseClass):

    def test_put_image(self):
        imageId = str(uuid4())
        reply = self.putImage(STANDARD_IMAGE, imageId)
        self.assertEqual(200, reply.statusCode)

    def test_head_image(self):
        """
            :description: Check image existence.
            :resources: '/images/{image_id}'
        """
        imageId = str(uuid4())
        self.putImage(STANDARD_IMAGE, imageId)
        reply = self.StoreApi.checkImage(BaseClass.DEFAULT_BUCKET, imageId)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.body, b'')

    def test_head_image_nonexists_imageid(self):
        """
            :description: Check image existence.
            :resources: '/images/{image_id}'
        """
        reply = self.StoreApi.checkImage(BaseClass.DEFAULT_BUCKET, str(uuid4()))
        self.assertEqual(reply.statusCode, 404)
        self.assertEqual(reply.body, b'')

    def test_non_jpg_format(self):
        imageId = str(uuid4())
        for pathToImage, imageFormat in IMAGE_NON_STANDARD_FORMATS.items():
            reply = self.putImage(pathToImage, imageId, imageFormat)
            self.assertEqual(200, reply.statusCode)

    def test_create_thumbnails(self):
        imageId = str(uuid4())
        for thumbnailsFlag in (0, 1):
            with self.subTest(createThumbnails = thumbnailsFlag):

                self.putImage(STANDARD_IMAGE, imageId = imageId, createThumbnails = thumbnailsFlag)
                time.sleep(3)
                for thumbnail in BaseClass.THUMBNAILS:
                    reply = self.getImage("{}_{}".format(imageId, thumbnail))
                    if thumbnailsFlag:
                        self.assertEqual(200, reply.statusCode)
                        self.assertThumbnail(thumbnail, reply.body)
                    else:
                        self.assertErrorRestAnswer(reply, 404, Error.ImageNotFoundError)

    def test_put_image_to_non_exist_bucket(self):
        image = createPayloadImg(STANDARD_IMAGE)
        for thumbnail in [0, 1]:
            with self.subTest():
                reply = self.StoreApi.putImage(image, imageId = str(uuid4()), bucketName = str(uuid4()),
                                               createThumbnails = thumbnail)
                self.assertErrorRestAnswer(reply, 404, Error.BucketNotFound)

    def test_bad_format_thumbnails(self):
        imageId = str(uuid4())
        reply = self.putImage(STANDARD_IMAGE, imageId, createThumbnails = 2)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams, msgFormat = ['thumbnails'])
        reply = self.putImage(STANDARD_IMAGE, imageId, createThumbnails = "q")
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams, msgFormat = ['thumbnails'])

    def test_bad_content_type(self):
        imageId = str(uuid4())
        reply = self.putImage(STANDARD_IMAGE, imageId, contentType = "application/json")
        self.assertErrorRestAnswer(reply, 400, Error.BadContentType)

    def test_bad_image(self):
        imageId = str(uuid4())
        reply = self.putImage(NON_IMAGE, imageId)
        self.assertErrorRestAnswer(reply, 400, Error.ConvertImageToJPGError)

    def test_delete_image(self):
        imageId = str(uuid4())
        self.putImage(STANDARD_IMAGE, imageId)

        reply = self.deleteImage(imageId)
        self.assertEqual(204, reply.statusCode)

        reply = self.getImage(imageId)
        self.assertEqual(404, reply.statusCode)

    def test_delete_non_exists_image(self):
        imageId = str(uuid4())
        reply = self.deleteImage(imageId)
        self.assertEqual(204, reply.statusCode)

    def test_get_image(self):
        imageId = str(uuid4())
        self.putImage(STANDARD_IMAGE, imageId)
        reply = self.getImage(imageId)
        self.assertGettingImage(STANDARD_IMAGE, reply)

    def test_get_non_exist_image(self):
        imageId = str(uuid4())
        reply = self.getImage(imageId)
        self.assertErrorRestAnswer(reply, 404, Error.ImageNotFoundError)
        reply = self.StoreApi.getImage(str(uuid4()), imageId)
        self.assertErrorRestAnswer(reply, 404, Error.ImageNotFoundError)
