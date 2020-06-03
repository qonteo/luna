from tornado import gen
from errors.error import Result, Error
from analytics.workers.tasks_functions import isTaskInProgress
from analytics.common_objects import logger, LUNA_CLIENT, timer
from analytics.luna_api_request_with_retry import makeRequestToLunaApiWithRetry
from common.tasks import TaskStatus
from lunavl import luna_api
from configs import config


class Matcher:
    """
    Class for cross-matching Luna API objects (descriptors or persons) with Luna API list.

    Attributes:
        matchFunc (function): function to use for matching
        listId (UUID4): the list id to match with
        references (list of UUID4): references list to match
        limit (int): how many results to return on every match
        task (Task): task to update the progress
        weigh (float): number is equal to time(cross-matching)/time(task)
        skipErrors (bool: skip errors or not (stop matching if an error occurred)
        iterByReferences (iterable): iter by references
        referencesType (str): references type - we use "identify" for matching persons and "match" for matching
            descriptors
    """
    def __init__(self, listId, references, limit, task, weightOfMatchingStep, skipErrors = False,
                 referencesType = 'descriptors'):
        """
        :param listId: the list id to match with
        :param references: references list to match
        :param limit: how many results to return on every match
        :param task: task to update the progress
        :param weightOfMatchingStep: number is equal to time(cross-matching)/time(task)
        :param skipErrors: skip errors or not (stop matching if an error occurred)
        :param referencesType: references type - we use "identify" for matching persons and "match" for matching
            descriptors
        """
        listRes = luna_api.getList(
            listId, 1, 1,
            '{}:{}/{}'.format(config.LUNA_API_HOST, config.LUNA_API_PORT, config.LUNA_API_API_VERSION),
            raiseError = True,
            token = config.LUNA_API_TOKEN)

        self.matchFunc = LUNA_CLIENT.match if "descriptors" in listRes.body else LUNA_CLIENT.identify
        self.listId = listId
        self.references = references
        self.matchLimit = limit
        self.task = task
        self.skipErrors = skipErrors
        self.weigh = weightOfMatchingStep
        self.iterByReferences = iter(references)
        self.referencesType = referencesType

    @gen.coroutine
    def _executeWorker(self):
        """
        Synchronous matcher function.

        :return: result
            Success with match results if succeed
            Fail if an error occurred
        """
        res = {}
        countDescriptors = len(self.references)

        paramName = {'descriptors': 'descriptorId', 'persons': 'personId'}[self.referencesType]
        matchArgs = {
            "request_function": self.matchFunc,
            "error_msg": "match {} by list".format(paramName),
            "listId": self.listId,
        }
        if self.matchLimit is not None:
            matchArgs["limit"] = self.matchLimit

        for reference in self.iterByReferences:
            self.task.progress += self.weigh * 1 / countDescriptors
            if not isTaskInProgress(self.task):
                return Result(Error.TaskCanceled, 0)

            matchArgs[paramName] = reference
            replyRes = yield makeRequestToLunaApiWithRetry(**matchArgs)

            if replyRes.fail:
                self.task.addError(replyRes)
                if not self.skipErrors:
                    self.task.status = TaskStatus.FAILED.value
                    logger.error("Failed  match with reply, stop task {}".format(self.task.id))
                    return replyRes

            res[reference] = replyRes.value['candidates']
        return Result(Error.Success, res)

    @timer.timerTor
    @gen.coroutine
    def match(self, concurrency = 5):
        """
        Concurrent matcher function.

        :param concurrency: count of synchronous functions to run.
        :return: result
            Success with match results if succeed
            Fail if an error occurred
        """
        matchResults = yield [self._executeWorker() for i in range(concurrency)]
        allSuccess = all(matchResult.success for matchResult in matchResults)
        if not allSuccess:
            errors = [matchResult.error for matchResult in matchResults if matchResult.fail]
            return Result(errors[0], 0)
        mergedResults = {}
        [mergedResults.update(r.value) for r in matchResults]

        return Result(Error.Success, mergedResults)
