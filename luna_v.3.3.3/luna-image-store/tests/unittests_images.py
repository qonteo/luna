from tests.base_class import BaseClass, createPayloadImg
from tests.config import SERVER_API_VERSION, SERVER_ORIGIN
from tests.resource import STANDARD_IMAGE, IMAGE_NON_STANDARD_FORMATS, NON_IMAGE
from luna_image_store.crutches_on_wheels.errors.errors import Error
import time
import requests
from uuid import uuid4
import json


class TestImages(BaseClass):

    def test_post_image(self):
        reply = self.postImage(STANDARD_IMAGE)
        self.assertPostingImageReply(reply)

    def test_non_jpg_format(self):
        for pathToImage, imageFormat in IMAGE_NON_STANDARD_FORMATS.items():
            reply = self.postImage(pathToImage, imageFormat)
            self.assertPostingImageReply(reply)

    def test_create_image_in_non_exist_bucket(self):
        image = createPayloadImg(STANDARD_IMAGE)
        for thumbnail in (0, 1):
            with self.subTest():
                reply = self.StoreApi.postImage(image, bucketName = str(uuid4()), createThumbnails = thumbnail)
                self.assertEqual(reply.statusCode, 404)
                self.assertErrorRestAnswer(reply, 404, Error.BucketNotFound)

    def test_create_thumbnails(self):
        for thumbnailFlag in (0, 1):
            with self.subTest(createThumbnails = thumbnailFlag):

                reply = self.postImage(STANDARD_IMAGE, createThumbnails = thumbnailFlag)
                self.assertPostingImageReply(reply)
                imageId = reply.json["image_id"]
                time.sleep(3)
                for thumbnail in BaseClass.THUMBNAILS:
                    reply = self.getImage("{}_{}".format(imageId, thumbnail))
                    if thumbnailFlag:
                        self.assertEqual(200, reply.statusCode)
                        self.assertThumbnail(thumbnail, reply.body)
                    else:
                        self.assertErrorRestAnswer(reply, 404, Error.ImageNotFoundError)

    def test_bad_format_thumbnails(self):
        reply = self.postImage(STANDARD_IMAGE, createThumbnails = 2)
        self.assertErrorRestAnswer(reply, 400,  Error.BadQueryParams, msgFormat = ['thumbnails'])
        reply = self.postImage(STANDARD_IMAGE, createThumbnails = "q")
        self.assertErrorRestAnswer(reply, 400,  Error.BadQueryParams, msgFormat = ['thumbnails'])

    def test_bad_content_type(self):
        reply = self.postImage(STANDARD_IMAGE, contentType = "application/json")
        self.assertErrorRestAnswer(reply, 400, Error.BadContentType)

    def test_bad_image(self):
        reply = self.postImage(NON_IMAGE)
        self.assertErrorRestAnswer(reply, 400, Error.ConvertImageToJPGError)

    def test_delete_images(self):
        imageIds = []
        for i in range(3):
            reply = self.postImage(STANDARD_IMAGE)
            self.assertPostingImageReply(reply)
            imageIds.append(reply.json["image_id"])

        reply = self.deleteImages(imageIds[:2])
        self.assertEqual(204, reply.statusCode)

        for i in range(2):
            reply = self.getImage(imageIds[i])
            self.assertErrorRestAnswer(reply, 404, Error.ImageNotFoundError)

        reply = self.getImage(imageIds[2])
        self.assertEqual(200, reply.statusCode)

        for i in range(1):
            reply = self.getImage(imageIds[i])
            self.assertEqual(404, reply.statusCode)


    def test_delete_non_exists_images(self):
        reply = self.postImage(STANDARD_IMAGE)
        self.assertPostingImageReply(reply)
        reply = self.deleteImages([reply.json["image_id"], str(uuid4())])
        self.assertEqual(204, reply.statusCode)

    def test_delete_images_with_break_json(self):
        url = "{}/{}/buckets/{}/images".format(SERVER_ORIGIN, SERVER_API_VERSION, BaseClass.DEFAULT_BUCKET)
        reply = requests.delete(url = url, data = "non json:")
        self.assertEqual(400, reply.status_code)
        self.assertDictEqual({"error_code": 12002, "detail": "Request does not contain json",
                              'desc': 'Bad/incomplete input data'}, json.loads(reply.text))

    def test_delete_images_with_bad_json(self):
        url = "{}/{}/buckets/{}/images".format(SERVER_ORIGIN, SERVER_API_VERSION, BaseClass.DEFAULT_BUCKET)
        reply = requests.delete(url = url, json = {"image": str(uuid4())})
        self.assertEqual(400, reply.status_code)
        self.assertDictEqual({"error_code": 12003, "detail": "Field 'images' not found in json",
                              'desc': 'Bad/incomplete input data'}, json.loads(reply.text))
