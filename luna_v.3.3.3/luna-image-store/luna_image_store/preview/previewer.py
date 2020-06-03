from tornado import gen
from configs.config import STORAGE_TYPE, THUMBNAILS
from image.image import resizeImage
from storage.local_storage.disk_driver import DiskDriver
from storage.aws_s3.s3_driver import S3Driver


class Previewer:

    def __init__(self, image, imageId, bucket, logger):

        self.image = image
        self.bucket = bucket
        self.logger = logger
        self.imageId = imageId
        self.storageContext = self.createStorageContext()

    def createStorageContext(self):
        if STORAGE_TYPE == "LOCAL":
            return DiskDriver(self.logger)
        elif STORAGE_TYPE == "S3":
            return S3Driver(self.logger)
        raise ValueError

    @gen.coroutine
    def makeThumbnails(self):
        for thumbnailSize in THUMBNAILS:
            thumbnailImage = resizeImage(self.image, thumbnailSize)
            yield self.storageContext.saveImage(thumbnailImage, "{}_{}".format(self.imageId, thumbnailSize), self.bucket)
            self.logger.debug("created thumbnail {} for size {}".format(thumbnailSize, self.imageId))
