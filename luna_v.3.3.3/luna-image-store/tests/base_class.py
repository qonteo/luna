import unittest
from tests.config import SERVER_ORIGIN, SERVER_API_VERSION
from PIL import Image
import io
from luna3.image_store.image_store import StoreApi
from time import sleep
from uuid import uuid4


def createPayloadImg(pathToPhoto):
    with open(pathToPhoto, "rb") as f:
        imgBytes = f.read()
    return imgBytes


class BaseClass(unittest.TestCase):
    TEST_BUCKET_POSTFIX = "-image-store-test"
    DEFAULT_BUCKET = "bucket" + TEST_BUCKET_POSTFIX

    THUMBNAILS = [32, 64, 96, 160]

    @classmethod
    def deleteTestBuckets(cls):
        for bucketName in cls.StoreApi.getBuckets().json:
            if bucketName.endswith(cls.TEST_BUCKET_POSTFIX):
                cls.StoreApi.deleteBucket(bucketName)

    @classmethod
    def generateBucketName(cls):
        return str(uuid4()) + cls.TEST_BUCKET_POSTFIX

    @classmethod
    def setUpClass(cls):
        cls.StoreApi = StoreApi(origin=SERVER_ORIGIN, api=SERVER_API_VERSION, )
        cls.deleteTestBuckets()
        sleep(0.2)
        reply = cls.StoreApi.createBucket(BaseClass.DEFAULT_BUCKET)
        if reply.statusCode not in [201, 409]:
            assert "Bucket did't create" == 0

    @classmethod
    def tearDownClass(cls):
        sleep(0.2)
        cls.deleteTestBuckets()

    def postImage(self, imagePath, contentType = "image/jpeg", createThumbnails = 0):
        image = createPayloadImg(imagePath)
        return self.StoreApi.postImage(image, BaseClass.DEFAULT_BUCKET, contentType, createThumbnails)

    def putImage(self, imagePath, imageId, contentType = "image/jpeg", createThumbnails = 0):
        image = createPayloadImg(imagePath)
        return self.StoreApi.putImage(image, imageId, BaseClass.DEFAULT_BUCKET, contentType, createThumbnails)

    def getImage(self, resource):
        return self.StoreApi.getImage(BaseClass.DEFAULT_BUCKET, resource)

    def deleteImages(self, ids):
        return self.StoreApi.deleteImages(BaseClass.DEFAULT_BUCKET, ids)

    def deleteImage(self, imageId):
        return self.StoreApi.deleteImage(BaseClass.DEFAULT_BUCKET, imageId)

    def assertCreatingBucketReoky(self, reply, bucket):
        self.assertEqual(201, reply.statusCode)
        self.assertEqual("/{}/buckets/{}/images".format(SERVER_API_VERSION, bucket), reply.headers["Location"])

    def assertErrorRestAnswer(self, reply, statusCode, error, msgFormat=None):
        self.assertEqual(reply.statusCode, statusCode)
        if msgFormat is None:
            self.assertEqual(reply.json["detail"], error.detail)
        else:
            self.assertEqual(reply.json["detail"], error.detail.format(*msgFormat))
        self.assertEqual(reply.json["error_code"], error.errorCode)
        self.assertEqual(reply.json["desc"], error.description)

    def assertPostingImageReply(self, reply):
        self.assertEqual(201, reply.statusCode)
        responseJson = reply.json
        self.assertIn("image_id", responseJson)
        imageId = responseJson["image_id"]
        self.assertEqual("/{}/buckets/{}/images/{}".format(SERVER_API_VERSION, BaseClass.DEFAULT_BUCKET, imageId),
                         reply.headers["Location"])

    def assertThumbnail(self, size, body):
        img = Image.open(io.BytesIO(body))
        width, height = img.size
        self.assertEqual(max(width, height), size)

    def assertGettingImage(self, path, reply):
        image = createPayloadImg(path)
        self.assertEqual(reply.body, image)