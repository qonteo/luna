from tornado import gen
from tornado.httpclient import HTTPResponse
from configs.config import CONNECT_TIMEOUT, REQUEST_TIMEOUT
from crutches_on_wheels.errors.errors import Error
from interface import implements
from logbook import Logger
from crutches_on_wheels.errors.exception import VLException
from storage.store_interface import StoreInterface, driverExceptionWarp
from storage.aws_s3 import s3
from lxml import objectify
from typing import Generator, List, Union


def raiseS3TornadoRequestError(reply: HTTPResponse, logger: Logger) -> None:
    """
    Generate Result with error by tornado request error.

    Args:
        reply: tornado request reply
        logger: logger
    Raises:
        VLException if unknown error from s3 or timeout or connection to s3 refused
    """
    if reply.request_time >= CONNECT_TIMEOUT or reply.request_time >= REQUEST_TIMEOUT:
        if reply.error.message == 'Timeout while connecting':
            logger.error(Error.ConnectTimeoutToS3Error.description)
            raise VLException(Error.ConnectTimeoutToS3Error)
        else:
            logger.error(Error.RequestTimeoutToS3Error.description)
            raise VLException(Error.RequestTimeoutToS3Error)
    if reply.error.__class__.__name__ == 'ConnectionRefusedError':
        logger.error(Error.S3ConnectionRefusedError.description)
        raise VLException(Error.S3ConnectionRefusedError)
    if hasattr(reply.error, "errno"):
        logger.error(reply.error.errno)
    raise VLException(Error.S3UnknownError)


def generateBodyForDeleteFromS3(fileList):
    """
    Generate s3 request body for removing files.

    :param fileList: files for removing
    :return: xml-string docs for request
    """
    res = '<?xml version="1.0" encoding="UTF-8"?><Delete>'
    for file in fileList:
        res += "<Object><Key>{}</Key></Object>".format(file)
    res += '</Delete>'
    return res


def raiseS3RequestError(reply, logger):
    """
    Generate Result with error by tornado request error.

    :param reply: tornado request reply
    :param logger: logger
    :raises: VLException
    """
    if reply.code == 403:
        logger.error("S3 request forbiden")
        raise VLException(Error.RequestS3Forbidden, 403, isCriticalError = False)
    elif reply.code == 404:
        logger.error("Bucket not found")
        raise VLException(Error.BucketNotFound, 404, isCriticalError = True)
    try:
        logger.error("S3 get error, status code: {}".format(str(reply.code)))
        logger.error("Response body: {}".format(reply.body.decode("utf-8")))
    except Exception:
        logger.exception()

    raise VLException(Error.RequestS3Error)


class S3Driver(implements(StoreInterface)):

    def __init__(self, logger):
        self.logger = logger

    @gen.coroutine
    def _saveFile(self, body: bytes, filename: str, bucket: str) -> Generator[None, None, None]:
        """
        Save file to bucket in S3

        :param body:  binary body
        :param filename: filename
        :param bucket: bucket
        """
        s3Ctx = s3.S3("PUT", "/" + filename, bucket, body)

        reply = yield s3Ctx.makeRequest()

        if 300 > reply.code >= 200:
            return
        elif reply.code == 599:
            raiseS3TornadoRequestError(reply, self.logger)
        raiseS3RequestError(reply, self.logger)

    @driverExceptionWarp(Error.SavingImageErrorS3)
    @gen.coroutine
    def saveImage(self, binaryImage, imageId, bucketName) -> Generator[None, None, None]:
        """
        Save image to bucket in S3

        :param binaryImage:  binary body
        :param imageId: image id
        :param bucketName: bucket name
        """
        yield self._saveFile(binaryImage, imageId + ".jpg", bucketName)

    @gen.coroutine
    def _checkFile(self, filename, bucket) -> Generator[None, None, bool]:
        """
        Check file existance in S3

        :param filename: filename
        :param bucket: bucket name
        :return: True of file exists else False
        """
        s3Ctx = s3.S3("HEAD", "/{}".format(filename), bucket)
        reply = yield s3Ctx.makeRequest()

        if 200 <= reply.code < 300:
            return True
        elif reply.code == 404:
            self.logger.debug("file {} not found".format(filename))
            return False

        elif reply.code == 599:
            raiseS3TornadoRequestError(reply, self.logger)
        raiseS3RequestError(reply, self.logger)

    @gen.coroutine
    def _getFile(self, filename, bucket) -> Generator[None, None, Union[bytes, None]]:
        """
        Get file from S3

        :param filename: filename
        :param bucket: bucket name
        :return: None if object not found else binary body
        """
        s3Ctx = s3.S3("GET", "/{}".format(filename), bucket)
        reply = yield s3Ctx.makeRequest()

        if 200 <= reply.code < 300:
            return reply.body
        elif reply.code == 404:
            self.logger.debug("file {} not found".format(filename))
            return None

        elif reply.code == 599:
            raiseS3TornadoRequestError(reply, self.logger)
        raiseS3RequestError(reply, self.logger)

    @driverExceptionWarp(Error.GettingImageErrorS3)
    @gen.coroutine
    def checkImage(self, imageId, bucketName) -> bool:
        """
        Check image exists in bucket

        :param imageId: image id
        :param bucketName: bucket name
        :return: true if image exists, else false
        """
        isImageExists = yield self._checkFile(imageId + ".jpg", bucketName)
        if isImageExists is None:
            raise VLException(Error.ImageNotFoundError, 404, isCriticalError = False)
        return isImageExists

    @driverExceptionWarp(Error.GettingImageErrorS3)
    @gen.coroutine
    def getImage(self, imageId, bucketName) -> Generator[None, None, bytes]:
        """
        Get image from bucket

        :param imageId: image id
        :param bucketName: bucket name
        :return: binary image
        """
        img = yield self._getFile(imageId + ".jpg", bucketName)
        if img is None:
            raise VLException(Error.ImageNotFoundError, 404, isCriticalError = False)
        return img

    @driverExceptionWarp(Error.DeleteImageErrorS3)
    @gen.coroutine
    def deleteImage(self, imageId, bucketName) -> Generator[None, None, List[str]]:
        """
        Delete image from s3

        :param imageId: image id
        :param bucketName: bucket name
        :return: [objectId] if image will not deleted else []
        """
        res = yield self.deleteImages([imageId], bucketName)
        return res

    @gen.coroutine
    def _deleteFilesFromS3(self, files: List[str], bucket: str) -> Generator[None, None, List[str]]:
        """
        Delete files from S3

        :param files: list of files
        :param bucket: bucket name
        :return: list non deleted files
        """
        bodyForRemove = generateBodyForDeleteFromS3(files)
        if s3.S3.S3_SIGNATURE_TYPE == "s3v2":
            s3Ctx = s3.S3("POST", "/", bucket, bodyForRemove, "delete")
        else:
            s3Ctx = s3.S3("POST", "/", bucket, bodyForRemove, "delete=")
        reply = yield s3Ctx.makeRequest()

        if reply.code >= 400:
            if reply.code == 599:
                return raiseS3TornadoRequestError(reply, self.logger)
            return raiseS3RequestError(reply, self.logger)

        rootXMLResponse = objectify.fromstring(reply.body)
        countErrors = 0
        nonDeleted = []
        if hasattr(rootXMLResponse, "Error"):
            for item in rootXMLResponse.Error:
                countErrors += 1
                self.logger.error(
                    "failed delete {}, code: {}, message: {}".format(item.Key, item.Code, item.Message))
                nonDeleted.append(item.Key)

        if not hasattr(rootXMLResponse, "Deleted"):
            self.logger.debug("Attribute 'Deleted' in s3 response not found")
        else:
            self.logger.debug("Count delete files in s3: {}".format(len(rootXMLResponse.Deleted)))
        return nonDeleted

    @driverExceptionWarp(Error.DeleteImagesErrorS3)
    @gen.coroutine
    def deleteImages(self, imageIds, bucketName) -> Generator[None, None, List[str]]:
        """
        Delete images from s3

        :param imageIds: image ids
        :param bucketName: bucket name
        :return: [objectId] list with non deleted images
        """
        files = [descriptorId + ".jpg" for descriptorId in imageIds]

        nonDeleted = yield self._deleteFilesFromS3(files, bucketName)
        return nonDeleted

    @driverExceptionWarp(Error.CreateBucketErrorS3)
    @gen.coroutine
    def createBucket(self, bucketName) -> None:
        """
        Create bucket

        Args:
            bucketName: bucket name
        """
        errorCode, errorMessage = s3.S3.createBucket(bucketName, self.logger)
        if errorCode is None:
            return
        elif errorCode in ('BucketAlreadyOwnedByYou', 'BucketAlreadyExists'):
            raise VLException(Error.BucketAlreadyExist, 409, isCriticalError = False)
        raise VLException(Error.generateError(Error.CreateBucketErrorS3, errorMessage))

    @driverExceptionWarp(Error.GettingBucketsErrorS3)
    @gen.coroutine
    def getBuckets(self) -> Generator[None, None, List[str]]:
        """
        Get list of all buckets

        Returns:
            list of buckets
        """
        lists, errorCode, errorMessage = s3.S3.getBuckets(self.logger)
        if errorCode is None:
            return lists
        raise VLException(Error.generateError(Error.GettingBucketsErrorS3, errorMessage))

    @driverExceptionWarp(Error.DeleteBucketsErrorS3)
    @gen.coroutine
    def deleteBucket(self, bucketName):
        errorCode, errorMessage = s3.S3.deleteBucket(bucketName, self.logger)
        if errorCode:
            raise VLException(Error.generateError(Error.DeleteBucketsErrorS3, errorMessage))

    @driverExceptionWarp(Error.SavingObjectErrorS3)
    @gen.coroutine
    def saveObject(self, objectBody, objectId, bucketName) -> Generator[None, None, None]:
        """
        Save object  to S3.

        Args:
            objectBody: object in bytes
            objectId: object id
            bucketName: bucket name
        """
        yield self._saveFile(objectBody, objectId, bucketName)

    @driverExceptionWarp(Error.GettingObjectErrorS3)
    @gen.coroutine
    def checkObject(self, objectId, bucketName) -> Generator[None, None, bool]:
        """
        Check object existance in S3

        Args:
            objectId: object Id
            bucketName: bucket name
        Returns:
            True if object exists, else False
        Raises:
            VLException(Error.ObjectInBucketNotFound, 404, isCriticalError = False): if object not found will raise
               exception.
        """
        isObjectExists = yield self._checkFile(objectId, bucketName)
        if isObjectExists is None:
            raise VLException(Error.ObjectNotFound, 404, isCriticalError = False)
        return isObjectExists

    @driverExceptionWarp(Error.GettingObjectErrorS3)
    @gen.coroutine
    def getObject(self, objectId, bucketName) -> Generator[None, None, bytes]:
        """
        Get object from S3

        Args:
            objectId: object Id
            bucketName: bucket name
        Returns:
            object in bytes
        Raises:
            VLException(Error.ObjectInBucketNotFound, 404, isCriticalError = False): if object not found will raise
               exception.
        """
        obj = yield self._getFile(objectId, bucketName)
        if obj is None:
            raise VLException(Error.ObjectInBucketNotFound, 404, isCriticalError = False)
        return obj

    @driverExceptionWarp(Error.DeleteObjectErrorS3)
    @gen.coroutine
    def deleteObject(self, objectId, bucketName) -> Generator[None, None, List[str]]:
        """
        Delete object from s3

        Args:
            objectId: object id
            bucketName: bucket name
        Returns:
            [objectId] if object will not deleted else []
        """
        res = yield self.deleteObjects([objectId], bucketName)
        return res

    @driverExceptionWarp(Error.DeleteObjectsErrorS3)
    @gen.coroutine
    def deleteObjects(self, objectIds, bucketName) -> Generator[None, None, List[str]]:
        """
        Delete objects from s3

        Args:
            objectIds: object ids
            bucketName: bucket name
        Returns:
            [objectId] list with non deleted objects
        """
        files = [objectId for objectId in objectIds]

        nonDeleted = yield self._deleteFilesFromS3(files, bucketName)
        return nonDeleted
