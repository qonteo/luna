from luna_image_store.crutches_on_wheels.errors.errors import Error
from tests.base_class import BaseClass


class TestBuckets(BaseClass):

    def tests_create_bucket(self):
        bucketName = self.generateBucketName()
        self.StoreApi.deleteBucket(bucketName)
        reply = self.StoreApi.createBucket(bucketName)
        self.assertCreatingBucketReoky(reply, bucketName)
        self.StoreApi.deleteBucket(bucketName)

    def tests_bucket_already_exist(self):
        reply = self.StoreApi.createBucket(BaseClass.DEFAULT_BUCKET)
        self.assertErrorRestAnswer(reply, 409, Error.BucketAlreadyExist)

    def tests_not_set_bucket(self):
        reply = self.StoreApi.createBucket()
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams, msgFormat = ['bucket'])

    def test_non_correct_symbols(self):
        reply = self.StoreApi.createBucket("{}-@".format(BaseClass.DEFAULT_BUCKET))
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams, msgFormat = ['bucket'])

    def test_getting_buckets(self):
        bucketName = self.generateBucketName()
        self.StoreApi.createBucket(bucketName)
        self.StoreApi.createBucket(BaseClass.DEFAULT_BUCKET)
        reply = self.StoreApi.getBuckets()
        self.assertIn(bucketName, reply.json)
        self.assertIn(BaseClass.DEFAULT_BUCKET, reply.json)
        self.StoreApi.deleteBucket(bucketName)
