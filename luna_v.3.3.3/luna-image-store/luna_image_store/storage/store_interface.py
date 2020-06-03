from functools import wraps

from interface import Interface
from tornado import gen
from crutches_on_wheels.errors.exception import VLException


class StoreInterface(Interface):
    """Interface for store drivers"""

    def __init__(self, logger):
        pass

    @gen.coroutine
    def saveImage(self, binaryImage, imageId, bucketName):
        """
        Save image.

        Args:
            bucketName: bucket name for storing image
            binaryImage: bimage bytes
            imageId: image id
        Raises:
            VLException
        """
        pass

    @gen.coroutine
    def checkImage(self, imageId, bucketName):
        """
        Check image exists in bucket

        Args:
            imageId: image id
            bucketName: bucket name
        Raises:
            VLException
        Returns:
            true if image exists, else false
        """
        pass

    @gen.coroutine
    def getImage(self, imageId, bucketName):
        """
        Get image by id.

        Args:
            bucketName: bucket name which store image
            imageId: image id
        Raises:
            VLException
        Returns:
            binary image
        """
        pass

    @gen.coroutine
    def deleteImage(self, imageId, bucketName):
        """
        Delete image by id from bucket.

        Args:
            bucketName: bucket name which store images
            imageId: image id
        Raises:
            VLException
        Returns:
            list with non delete images
        """
        pass

    @gen.coroutine
    def deleteImages(self, imageIds, bucketName):
        """
        Delete list images

        Args:
            imageIds: images id
            bucketName: bucket name
        Raises:
            VLException
        """
        pass

    @gen.coroutine
    def createBucket(self, bucketName):
        """
        Create bucket for images

        Args:
            bucketName: bucket name
        Raises:
            VLException
        """
        pass

    @gen.coroutine
    def getBuckets(self):
        """
        Getting list of exist buckets

        Raises:
            VLException
        Returns:
            ["bucket_1", "bucket_2"]
        """
        pass

    @gen.coroutine
    def deleteBucket(self, bucketName):
        """
        Getting list of exist buckets

        Args:
            bucketName: bucket name
        Raises:
            VLException
        """
        pass

    @gen.coroutine
    def saveObject(self, objectBody, objectId, bucketName):
        """
        Save object

        Args:
            objectBody: object, available: text, json
            objectId: object id
            bucketName: bucket name which store object
        Raises:
            VLException
        """
        pass

    @gen.coroutine
    def checkObject(self, objectId, bucketName):
        """
        Check object exists in bucket

        Args:
            objectId: image id
            bucketName: bucket name
        Raises:
            VLException
        Returns:
            true if image exists, else false
        """
        pass

    @gen.coroutine
    def getObject(self, objectId, bucketName):
        """
        Get object by id

        Args:
            objectId: object id
            bucketName: bucket name which store object
        Raises:
            VLException
        Returns:
            json/text
        """
        pass

    @gen.coroutine
    def deleteObject(self, objectId, bucketName):
        """
        Delete object by id from bucket

        Args:
            objectId: object id
            bucketName: bucket name which store object
        Raises:
            VLException
        """
        pass

    @gen.coroutine
    def deleteObjects(self, objectIds, bucketName):
        """
        Delete list of objects by ids from bucket

        Args:
            objectIds: list of object ids
            bucketName: bucket name which store object
        Raises:
            VLException
        """
        pass


def driverExceptionWarp(error):
    """
    Decorator for catching exceptions in asynchronous request.

    Args:
        error: returning error in the exception case
    Returns:
        if exception was caught, system calls error method with error
    """

    def realWarp(func):
        @wraps(func)
        @gen.coroutine
        def wrap(*func_args, **func_kwargs):
            try:
                res = yield func(*func_args, **func_kwargs)
                return res
            except VLException:
                raise
            except Exception as e:
                func_args[0].logger.exception()
                raise VLException(error, exception=e)

        return wrap

    return realWarp
