from tornado import gen
from errors.error import Result, Error
from analytics.workers.tasks_functions import isTaskInProgress
from analytics.luna_api_request_with_retry import makeRequestToLunaApiWithRetry
from analytics.common_objects import LUNA_CLIENT, logger


class ListLinker:
    """
    Class to link Luna API objects (persons or descriptors) to another Luna API list.

    Attributes:
        listId (UUID4): Luna API list id to link to
        linkerType (str): "descriptors" or "persons"
        references (list of UUID4): reference (descriptor or person) list
        task (Task): task
        nextReferenceIdx (int): the current reference counter
        weight (float): number is equal to time(linking)/time(task)
        skipErrors (bool): skip errors or not (stop linking if an error occurred)
        lunaLinkerFunction (function): function to use for linking
        error (ErrorInfo): error to write if cannot link
    """
    def __init__(self, listId, linkerType, references, task, weightOfLinkerStep, skipErrors=True):
        """
        :param listId: list_id to link objects with
        :param linkerType: result objects type
        :param references: list of references (persons or descriptors)
        :param task: task to update the progress
        :param weightOfLinkerStep: number is equal to time(linking)/time(task)
        :param skipErrors: skip errors or not (stop linking if an error occurred)
        """
        self.listId = listId
        self.linkerType = linkerType
        self.references = references
        self.task = task
        self.nextReferenceIdx = 0
        self.weight = weightOfLinkerStep
        self.skipErrors = skipErrors
        self.lunaLinkerFunction = {
            'descriptors': LUNA_CLIENT.linkListToDescriptor,
            'persons': LUNA_CLIENT.linkListToPerson,
        }[self.linkerType]
        self.error = {
            "descriptors": Error.LinkDescriptorError,
            "persons": Error.LinkPersonError
        }[self.linkerType]

    @gen.coroutine
    def _executeWorker(self):
        """
        Synchronous linker function.

        :return: result
            Success with link result list if succeed
            Fail if an error occurred
        """
        results = []
        for i in range(len(self.references) + 1):
            if self.nextReferenceIdx == len(self.references):
                break
            self.task.progress += self.weight * 1 / len(self.references)
            if not isTaskInProgress(self.task):
                return Result(Error.TaskCanceled, 0)

            reference = self.references[self.nextReferenceIdx]
            self.nextReferenceIdx += 1
            linkRes = yield makeRequestToLunaApiWithRetry(
                self.lunaLinkerFunction,
                'Link {}'.format(self.linkerType),
                reference,
                self.listId,
            )
            if linkRes.success:
                results += [Result(Error.Success, reference)]
            else:
                msg = (self.error.getErrorDescription() + ': "{}"').format(reference, self.listId, linkRes.value)
                res = Result(Error.generateError(self.error, msg), linkRes.value)
                self.task.addError(res)
                if self.skipErrors:
                    results += [res]
                else:
                    return res
        else:
            logger.error("Exceeded number of operations for match descriptors with list")
            return Result(Error.UnknownError, results)
        return Result(Error.Success, results)

    @gen.coroutine
    def link(self, concurrency=3):
        """
        Concurrent linker function.

        :param concurrency: count of synchronous functions to run.
        :return: result
            Success with link result list if succeed
            Fail if an error occurred
        """
        linkObjectRes = yield [self._executeWorker() for i in range(concurrency)]
        if any(res.fail for res in linkObjectRes):
            return next(res for res in linkObjectRes if res.fail)
        results = [r for res in linkObjectRes for r in res.value]
        return Result(Error.Success, results)
