from uuid import uuid4

from tests.base_class import BaseClass


class TestBucket(BaseClass):

    def tests_delete_bucket(self):
        """
            :description: Delete bucket.
            :resources: '/buckets/{bucketName}'
        """
        bucketName = self.generateBucketName()
        self.StoreApi.createBucket(bucketName)

        reply = self.StoreApi.deleteBucket(bucketName)
        self.assertEqual(reply.statusCode, 202)

        reply = self.StoreApi.getBuckets(bucketName)
        self.assertNotIn(bucketName, reply.json)
