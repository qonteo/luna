from tests.base_class import BaseClass
from luna_image_store.crutches_on_wheels.errors.errors import Error
from uuid import uuid4


class TestObjects(BaseClass):

    def test_post_object(self):
        reply = self.StoreApi.postObject(objectBody = '["test"]', bucketName = BaseClass.DEFAULT_BUCKET)
        self.assertEqual(201, reply.statusCode)

    def test_post_image_wrong_content_type(self):
        reply = self.StoreApi.postObject(objectBody = 'test', bucketName = BaseClass.DEFAULT_BUCKET,
                                         contentType = 'image/jpeg')
        self.assertErrorRestAnswer(reply, 415, Error.UnsupportedMediaType)

    def test_post_text_as_json(self):
        reply = self.StoreApi.postObject(objectBody = 'test', bucketName = BaseClass.DEFAULT_BUCKET,
                                         contentType = 'application/json')
        self.assertErrorRestAnswer(reply, 400, Error.SpecifiedTypeNotMatchDataType)

    def test_post_object_empty(self):
        reply = self.StoreApi.postObject(objectBody = None, bucketName = BaseClass.DEFAULT_BUCKET)
        self.assertErrorRestAnswer(reply, 400, Error.BadBody)

    def test_post_object_to_non_existing_bucket(self):
        reply = self.StoreApi.postObject(objectBody = '["test"]', bucketName = str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.BucketNotFound)

    def test_delete_objects(self):
        objectIds = []
        for _ in range(3):
            reply = self.StoreApi.postObject(objectBody = '["test"]', bucketName = BaseClass.DEFAULT_BUCKET)
            self.assertEqual(201, reply.statusCode)
            objectIds.append(reply.json["object_id"])

        reply = self.StoreApi.deleteObjects(BaseClass.DEFAULT_BUCKET, objectIds[:2])
        self.assertEqual(204, reply.statusCode)

        for i in range(2):
            reply = self.StoreApi.getObject(BaseClass.DEFAULT_BUCKET, objectIds[i])
            self.assertErrorRestAnswer(reply, 404, Error.ObjectInBucketNotFound)

        reply = self.StoreApi.getObject(BaseClass.DEFAULT_BUCKET, objectIds[2])
        self.assertEqual(200, reply.statusCode)

        for i in range(1):
            reply = self.getImage(objectIds[i])
            self.assertEqual(404, reply.statusCode)

    def test_delete_non_existing_objects(self):
        reply = self.StoreApi.deleteObjects(bucketName = BaseClass.DEFAULT_BUCKET,
                                            objectIds = [str(uuid4()), str(uuid4())])
        self.assertEqual(204, reply.statusCode)
