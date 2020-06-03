from tests.base_class import BaseClass
from luna_image_store.crutches_on_wheels.errors.errors import Error
from uuid import uuid4


class TestObject(BaseClass):

    def test_put_object(self):
        reply = self.StoreApi.putObject(objectBody = '["test"]', objectId = str(uuid4()),
                                        bucketName = BaseClass.DEFAULT_BUCKET)
        self.assertEqual(200, reply.statusCode)

    def test_head_object(self):
        """
            :description: Check object existence.
            :resources: '/objects/{object_id}'
        """
        objectId = str(uuid4())
        self.StoreApi.putObject(objectBody='["test"]', objectId=objectId,
                                bucketName=BaseClass.DEFAULT_BUCKET)
        reply = self.StoreApi.checkObject(BaseClass.DEFAULT_BUCKET, objectId, acceptType='text/plain')
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.body, b'')

    def test_head_object_nonexists_objectid(self):
        """
            :description: Check object existence.
            :resources: '/objects/{object_id}'
        """
        reply = self.StoreApi.checkObject(BaseClass.DEFAULT_BUCKET, str(uuid4()), acceptType='application/json')
        self.assertEqual(reply.statusCode, 404)
        self.assertEqual(reply.body, b'')

    def test_put_object_wrong_content_type(self):
        reply = self.StoreApi.putObject(objectBody = '["test"]', objectId = str(uuid4()),
                                        bucketName = BaseClass.DEFAULT_BUCKET, contentType = 'image/jpeg')
        self.assertErrorRestAnswer(reply, 415, Error.UnsupportedMediaType)

    def test_put_text_as_json(self):
        reply = self.StoreApi.putObject(objectBody = 'test', objectId = str(uuid4()),
                                        bucketName = BaseClass.DEFAULT_BUCKET, contentType = 'application/json')
        self.assertErrorRestAnswer(reply, 400, Error.SpecifiedTypeNotMatchDataType)

    def test_put_object_empty(self):
        reply = self.StoreApi.putObject(objectBody = None, objectId = str(uuid4()),
                                        bucketName = BaseClass.DEFAULT_BUCKET)
        self.assertErrorRestAnswer(reply, 400, Error.BadBody)

    def test_put_object_to_non_existing_bucket(self):
        reply = self.StoreApi.putObject(objectBody = '["test"]', objectId = str(uuid4()), bucketName = str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.BucketNotFound)

    def test_delete_object(self):
        objectId = str(uuid4())
        self.StoreApi.putObject(objectBody = 'test', objectId = objectId, bucketName = BaseClass.DEFAULT_BUCKET)

        reply = self.StoreApi.deleteObject(BaseClass.DEFAULT_BUCKET, objectId)
        self.assertEqual(204, reply.statusCode)

        reply = self.getImage(objectId)
        self.assertEqual(404, reply.statusCode)

    def test_delete_non_existing_object(self):
        reply = self.StoreApi.deleteObject(bucketName = BaseClass.DEFAULT_BUCKET, objectId = str(uuid4()))
        self.assertEqual(204, reply.statusCode)

    def test_get_object(self):
        objectId = str(uuid4())
        self.StoreApi.putObject(objectBody='["test"]', objectId=objectId, bucketName=BaseClass.DEFAULT_BUCKET)
        reply = self.StoreApi.getObject(objectId=objectId, bucketName=BaseClass.DEFAULT_BUCKET)
        self.assertEqual(200, reply.statusCode)

    def test_get_text_object_as_text(self):
        objectId = str(uuid4())
        r = self.StoreApi.putObject(objectBody = 'test', objectId = objectId, bucketName = BaseClass.DEFAULT_BUCKET,
                                    contentType = 'text/plain')

        reply = self.StoreApi.getObject(bucketName = BaseClass.DEFAULT_BUCKET, objectId = objectId,
                                        acceptType = 'text/plain')
        self.assertEqual(200, reply.statusCode)

    def test_get_json_object_as_json(self):
        objectId = str(uuid4())
        self.StoreApi.putObject(objectBody = '["test"]', objectId = objectId, bucketName = BaseClass.DEFAULT_BUCKET)

        reply = self.StoreApi.getObject(bucketName = BaseClass.DEFAULT_BUCKET, objectId = objectId)
        self.assertEqual(200, reply.statusCode)

    def test_get_text_object_as_json(self):
        objectId = str(uuid4())
        r = self.StoreApi.putObject(objectBody = 'test', objectId = objectId, bucketName = BaseClass.DEFAULT_BUCKET,
                                    contentType = 'text/plain')

        reply = self.StoreApi.getObject(bucketName = BaseClass.DEFAULT_BUCKET, objectId = objectId,
                                        acceptType = 'application/json')
        self.assertErrorRestAnswer(reply, 406, Error.NotAcceptable)

    def test_get_json_object_as_text(self):
        objectId = str(uuid4())
        self.StoreApi.putObject(objectBody = '["test"]', objectId = objectId, bucketName = BaseClass.DEFAULT_BUCKET)

        reply = self.StoreApi.getObject(bucketName = BaseClass.DEFAULT_BUCKET, objectId = objectId,
                                        acceptType = 'text/plain')
        self.assertEqual(reply.statusCode, 200)

    def test_get_non_existing_object(self):
        objectId = str(uuid4())
        reply = self.StoreApi.getObject(bucketName = BaseClass.DEFAULT_BUCKET, objectId = objectId)
        self.assertErrorRestAnswer(reply, 404, Error.ObjectInBucketNotFound)
