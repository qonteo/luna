from tornado import gen
from analytics.common_objects import LUNA_CLIENT, logger
from analytics.luna_api_request_with_retry import makeRequestToLunaApiWithRetry
from analytics.workers.tasks_functions import isTaskInProgress
from errors.error import Result, Error


def referenceDescription(reference):
    """
    Error description id generation.

    :param reference: reference object dict
    :return: string with "<object type> <object id>" format
    """
    if 'group_id' in reference:
        return "group " + reference['group_id']
    elif 'event_id' in reference:
        return "event " + reference['event_id']
    else:
        return "descriptor " + next(iter(reference['descriptors']))


class Personalizator:
    """
    Class to make persons from batches of descriptors.

    Attributes:
        references (list of UUID4): descriptor list list
        task (Task): task to update the progress
        nextReferenceIdx (int): the current descriptor list counter
        weight (float): number is equal to time(personalise)/time(task)
        skipErrors (bool): skip errors or not (stop making persons if an error occurred)
    """
    def __init__(self, referencesLists: list, task, weightOfPersonalizatorStep, skipErrors=True):
        self.references = referencesLists
        self.task = task
        self.nextReferenceIdx = 0
        self.weight = weightOfPersonalizatorStep
        self.skipErrors = skipErrors

    @gen.coroutine
    def executeWorker(self):
        """
        Synchronous Personalizer function.

        :return: result
            Success with occurred errors if succeed
            Fail if an error occurred
        """
        res = []
        for i in range(len(self.references)+1):
            if self.nextReferenceIdx == len(self.references):
                break
            self.task.progress += self.weight * 1 / len(self.references)
            if not isTaskInProgress(self.task):
                return Result(Error.TaskCanceled, 0)
            reference = self.references[self.nextReferenceIdx]
            descriptors = reference['descriptors']
            self.nextReferenceIdx += 1

            personRes = yield makeRequestToLunaApiWithRetry(
                LUNA_CLIENT.createPerson,
                'Cannot create person',
                raiseError=not self.skipErrors
            )
            if not personRes.success:
                res += [Result(Error.UnknownError, 0)]
                continue
            personId = personRes.value['person_id']

            errors_descriptors = []
            for descriptorId in descriptors:
                linkRes = yield makeRequestToLunaApiWithRetry(
                    LUNA_CLIENT.linkDescriptorToPerson,
                    "Cannot link descriptor '{}' with person '{}' for '{}'".format(descriptorId, personId,
                                                                                   referenceDescription(reference)),
                    personId,
                    descriptorId,
                    raiseError=not self.skipErrors
                )
                if not linkRes.success:
                    errors_descriptors += [linkRes]
            if not errors_descriptors:
                reference['person_id'] = personId
                res += [Result(Error.Success, reference)]
            else:
                errors = [Result(Error.generateError(Error.LinkDescriptorToPersonError, error.description), error)
                          for error in errors_descriptors]
                res += errors
                [self.task.addError(error) for error in errors]
        else:
            logger.error("Exceeded number operation for match descriptors with list")
            return Result(Error.UnknownError, 0)
        return Result(Error.Success, res)

    @gen.coroutine
    def personalize(self, concurrency=3):
        """
        Concurrent Personalizer function.

        :param concurrency: count of synchronous functions to run.
        :return: result
            Success with occurred errors if succeed
            Fail if an error occurred
        """
        persRes = yield [self.executeWorker() for i in range(concurrency)]
        if any(res.fail for res in persRes):
            return next(res for res in persRes if res.fail)
        persRes = [r for res in persRes for r in res.value]
        return Result(Error.Success, persRes)
