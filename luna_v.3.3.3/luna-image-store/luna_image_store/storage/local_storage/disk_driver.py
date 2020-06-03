import os
import shutil

from crutches_on_wheels.errors.exception import VLException
from storage.store_interface import StoreInterface, driverExceptionWarp
from interface import implements
from tornado import gen
from configs.config import LOCAL_STORAGE
from crutches_on_wheels.errors.errors import Error


def getPathToFolderWithFile(imageId, bucket) -> str:
    """
    Getting path to folder with image.

    If you work in *unix system in one folder must be <50k files.

    :param bucket: bucket name
    :param imageId: name of file
    :return: return string *LOCATION + "/" + descriptorId[-2:] + "/"*
    """
    path = os.path.join(LOCAL_STORAGE, bucket, imageId[:4], '')
    return path


def getAbsPath(fileName, bucket) -> str:
    """
    Getting absolute path to file.

    :param fileName: filename without extension.
    :param bucket: bucket
    :return: return string
    """
    relativePath = getPathToFolderWithFile(fileName, bucket) + fileName + ".jpg"
    return os.path.abspath(relativePath)


def getAbsFilePath(fileName, bucket) -> str:
    """
    Getting absolute path to file.

    :param fileName: filename with extension.
    :param bucket: bucket
    :return: return string
    """
    relativePath = getPathToFolderWithFile(fileName, bucket) + fileName
    return os.path.abspath(relativePath)


def isBucketExist(bucket) -> bool:
    """
    Checking exist or not folder with name *bucket* in *LOCAL_STORAGE*.

    :param bucket: bucket name
    :return: return true if exist otherwise false
    """
    return os.path.exists(os.path.join(LOCAL_STORAGE, bucket))


class DiskDriver(implements(StoreInterface)):

    def __init__(self, logger):
        self.logger = logger

    @driverExceptionWarp(Error.SavingImageErrorLocal)
    @gen.coroutine
    def saveImage(self, binaryImage, imageId, bucketName):
        if not isBucketExist(bucketName):
            raise VLException(Error.BucketNotFound, 404, isCriticalError = False)
        path = getPathToFolderWithFile(imageId, bucketName)
        if not os.path.exists(path):
            os.makedirs(path)
        f = open(getAbsPath(imageId, bucketName), 'wb')
        f.write(binaryImage)
        f.close()

    @staticmethod
    def _checkFile(fileId, bucketName) -> bool:
        pathToFile = getAbsFilePath(fileId, bucketName)
        return os.path.isfile(pathToFile)

    @driverExceptionWarp(Error.GettingImageErrorLocal)
    @gen.coroutine
    def checkImage(self, imageId, bucketName):
        return self._checkFile(imageId+'.jpg', bucketName)

    @driverExceptionWarp(Error.GettingImageErrorLocal)
    @gen.coroutine
    def getImage(self, imageId, bucketName):
        pathToImg = getAbsPath(imageId, bucketName)
        if os.path.isfile(pathToImg):
            with open(pathToImg, "rb") as f:
                imgBytes = f.read()
            return imgBytes
        else:
            raise VLException(Error.ImageNotFoundError, 404, isCriticalError = False)

    @driverExceptionWarp(Error.DeleteImageErrorLocal)
    @gen.coroutine
    def deleteImage(self, imageId, bucketName):
        try:
            if not isBucketExist(bucketName):
                raise VLException(Error.BucketNotFound, 404, isCriticalError = False)
            os.remove(getAbsPath(imageId, bucketName))
        except FileNotFoundError:
            self.logger.debug("File {} not found".format(imageId))

    @driverExceptionWarp(Error.DeleteImagesErrorLocal)
    @gen.coroutine
    def deleteImages(self, imageIds, bucketName):
        for image in imageIds:
            yield self.deleteImage(image, bucketName)

    @driverExceptionWarp(Error.CreateBucketErrorLocal)
    @gen.coroutine
    def createBucket(self, bucketName):
        if isBucketExist(bucketName):
            raise VLException(Error.BucketAlreadyExist, 409, isCriticalError = False)
        path = os.path.join(LOCAL_STORAGE, bucketName)
        if not os.path.exists(path):
            os.makedirs(path)

    @driverExceptionWarp(Error.GettingBucketsErrorLocal)
    @gen.coroutine
    def getBuckets(self):
        buckets = os.listdir(LOCAL_STORAGE)
        return buckets

    @driverExceptionWarp(Error.DeleteBucketErrorLocal)
    @gen.coroutine
    def deleteBucket(self, bucketName):
        path = os.path.join(LOCAL_STORAGE, bucketName)
        shutil.rmtree(path)

    @driverExceptionWarp(Error.SavingObjectErrorLocal)
    @gen.coroutine
    def saveObject(self, objectBody, objectId, bucketName):
        if not isBucketExist(bucketName):
            raise VLException(Error.BucketNotFound, 404, isCriticalError = False)
        path = getPathToFolderWithFile(objectId, bucketName)
        if not os.path.exists(path):
            os.makedirs(path)
        f = open(getAbsFilePath(objectId, bucketName), 'wb')
        f.write(objectBody)
        f.close()

    @driverExceptionWarp(Error.GettingObjectErrorLocal)
    @gen.coroutine
    def checkObject(self, objectId, bucketName):
        return self._checkFile(objectId, bucketName)

    @driverExceptionWarp(Error.GettingObjectErrorLocal)
    @gen.coroutine
    def getObject(self, objectId, bucketName):
        path = getAbsFilePath(objectId, bucketName)
        if os.path.isfile(path):
            with open(path, "rb") as f:
                objectBody = f.read()
            return objectBody
        else:
            raise VLException(Error.ObjectInBucketNotFound, 404, isCriticalError = False)

    @driverExceptionWarp(Error.DeleteObjectErrorLocal)
    @gen.coroutine
    def deleteObject(self, objectId, bucketName):
        try:
            if not isBucketExist(bucketName):
                raise VLException(Error.BucketNotFound, 404, isCriticalError = False)
            os.remove(getAbsFilePath(objectId, bucketName))
        except FileNotFoundError:
            self.logger.debug("File {} not found".format(objectId))

    @driverExceptionWarp(Error.DeleteObjectsErrorLocal)
    @gen.coroutine
    def deleteObjects(self, objectIds, bucketName):
        for objectId in objectIds:
            yield self.deleteObject(objectId, bucketName)
