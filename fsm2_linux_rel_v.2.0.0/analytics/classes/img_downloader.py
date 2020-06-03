from tornado import gen
from errors.error import Result, Error
from analytics.workers.tasks_functions import isTaskInProgress
from analytics.common_objects import logger, LUNA_CLIENT, timer
from analytics.luna_api_request_with_retry import makeRequestToLunaApiWithRetry
from common.tasks import TaskStatus, Task
import os
LOCATION = "./storage/portraits"


def getPathDirectory(descriptorId):
    """
    Getting path to image.

    If you work in *unix system in one folder must be <50k files.

    :param descriptorId: id of descriptors
    :return: return string *LOCATION + "/" + descriptorId[-2:] + "/"*
    """
    path = os.path.join(LOCATION, descriptorId[-2:], '')
    return path


def getPath(descriptorId):
    """
    Getting path to folder with image.

    If you work in *unix system in one folder must be <50k files.

    :param descriptorId: id of descriptors
    :return: return string *LOCATION + "/" + descriptorId[-2:] + "/" + descriptorId + ",jpg" *
    """
    path = os.path.join(getPathDirectory(descriptorId), descriptorId + '.jpg')
    return path


class ImgDownloader:
    """
    Class for upload to hard disk images

    Attributes:
        descriptors (list of UUID4): photo id list to download
        task (Task): task
        skipErrors (bool): if to skip errors
        weigh (float): number is equal to time(uploading)/time(task)
        iterByDescriptors (iterator): descriptors iterator
        failedDownloadPortraits (list of UUID4): list of photo ids that are not loaded
        successDownloadPortraits (list of UUID4): list of photo ids that are loaded
    """
    def __init__(self, descriptorsIds, task, weightOfUploadinginTask, skipErrors = True):
        """
        :param descriptorsIds: list of descriptors ids for uploading
        :type descriptorsIds: list
        :param task: task
        :type task: Task
        :param weightOfUploadinginTask: number is equal to time(uploading)/time(task)
        :type weightOfUploadinginTask: float
        :param skipErrors: skip or not error in processing uploading
        :type skipErrors: bool
        """

        self.descriptors = descriptorsIds
        self.task = task
        self.skipErrors = skipErrors
        self.weigh = weightOfUploadinginTask
        self.iterByDescriptors = iter(descriptorsIds)
        self.failedDownloadPortraits = []
        self.successDownloadPortraits = []

    @staticmethod
    def checkExistPortrait(descriptor):
        """
        Check exist portrait on disk or not

        :param descriptor: id of descriptor.
        :rtype: bool
        :return: True if file "/portraits/<descriptor>.jpg" exist else False
        """
        path = getPathDirectory(descriptor)
        return os.path.isfile("{}{}.jpg".format(path, descriptor))

    @staticmethod
    def savePortraits(descriptorId, img):
        """
        Save portrait to disk.

        :param descriptorId: id of descriptor
        :param img: binary img
        """
        path = getPathDirectory(descriptorId)
        if not os.path.exists(path):
            os.makedirs(path)
        with open("{}{}.jpg".format(path, descriptorId), 'wb') as f:
            f.write(img)

    @gen.coroutine
    def executeWorker(self):
        """
        Internal function, worker for asynchronous download portraits from luna api. Worker takes next descriptor
        which is not downloaded and downloads its portrait.

        :return: result
            Success if succeed
            Fail if an error occurred
        """
        countDescriptors = len(self.descriptors)

        for descriptor in self.iterByDescriptors:

            self.task.progress += self.weigh * 1 / countDescriptors
            if not isTaskInProgress(self.task):
                return Result(Error.TaskCanceled, 0)

            if ImgDownloader.checkExistPortrait(descriptor):
                self.successDownloadPortraits.append(descriptor)
                continue

            replyRes = yield makeRequestToLunaApiWithRetry(LUNA_CLIENT.getPortrait, "download portraits",
                                                           descriptorId = descriptor)
            if replyRes.fail and not self.skipErrors:
                self.task.status = TaskStatus.FAILED.value
                logger.error("Failed  match with reply, stop task {}".format(self.task.id))
                self.task.addError(replyRes)
                return replyRes
            if replyRes.success:
                ImgDownloader.savePortraits(descriptor, replyRes.value)
                self.successDownloadPortraits.append(descriptor)
            else:
                self.failedDownloadPortraits.append(descriptor)
        return Result(Error.Success, 0)

    @timer.timerTor
    @gen.coroutine
    def download(self, concurrency = 10):
        """
        Run portrait downloads.

        :param concurrency: count of synchronous functions to run
        :return: result
            Success with tuple (<success downloaded ids>, <failed downloaded ids>)
            Fail if an error occurred
        """
        downloadResults = yield [self.executeWorker() for i in range(concurrency)]
        allSuccess = all(downloadResult.success for downloadResult in downloadResults)
        if not allSuccess:
            errors = [upload.error for upload in downloadResults if upload.fail]
            return Result(errors[0], 0)
        return Result(Error.Success, (self.successDownloadPortraits, self.failedDownloadPortraits))
