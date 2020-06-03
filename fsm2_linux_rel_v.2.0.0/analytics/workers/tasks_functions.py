from tornado import gen
from common.tasks import TaskStatus, Task
from analytics.common_objects import ES_CLIENT, LUNA_CLIENT

from errors.error import Error, Result
import time
from tornado.ioloop import IOLoop


def isTaskInProgress(task: Task):
    """
    Check if one need task to stop.

    :param task: task
    :return: stop or not
    """
    return task.status == TaskStatus.IN_PROGRESS.value


@gen.coroutine
def flushFailedTask(task: Task, errorResult, location):
    """
    Change task status and add the error.

    :param task: task to finish
    :param errorResult: result with an error
    :param location: location of the finished task
    :return: None
    """
    if errorResult.error == Error.TaskCanceled:
        return
    yield gen.sleep(2)                                      #: wait a synchronization of schards in ES
    task.status = TaskStatus.FAILED.value
    task.addError(errorResult)
    yield ES_CLIENT.markTaskDone(task, location)


def periodicUpdateTaskProgress(task, timeout):
    """
    Update the current task into es while task.status is "in progress".

    :param task: task to update
    :param timeout: timeout between updates
    :return: None
    """
    @gen.coroutine
    def update():
        if task.status != TaskStatus.IN_PROGRESS.value:
            return
        yield ES_CLIENT.updateTaskProgress(task.id, task.progress)
        periodicUpdateTaskProgress(task, timeout)

    IOLoop.current().add_timeout(time.time() + timeout, update)


def periodicUpdateTaskStatus(task, timeout):
    """
    Update the current task status from the es while task.status is "in progress".

    :param task: task to update
    :param timeout: timeout between updates
    :return: None
    """
    @gen.coroutine
    def update():
        if not isTaskInProgress(task):
            return
        statusRes = yield ES_CLIENT.getTask(task.id)
        if statusRes.success and task.status == TaskStatus.IN_PROGRESS.value:
            if "Location" in statusRes.value:
                task.status = TaskStatus.CANCELED.value
        periodicUpdateTaskStatus(task, timeout)

    IOLoop.current().add_timeout(time.time() + timeout, update)


@gen.coroutine
def pretendConcurrent(f, argsList, concurrency=3):
    """
    Call several concurrent workers to run the function f.
    !!!WARNING!!! The order can be violated.

    :param f: function to call
    :param argsList: args list
    :param concurrency: number of the concurrent workers
    :return: result list
    """
    argsIter = iter(argsList)
    results = []

    @gen.coroutine
    def concurrentF():
        """
        One async worker.
        :return: None
        """
        for args in argsIter:
            result = yield f(*args)
            results.append(result)
    yield [concurrentF() for i in range(concurrency)]
    return results


@gen.coroutine
def getFullLunaList(listId, concurrency=3):
    """
    Get full Luna API list content.

    :param listId:
    :param concurrency:
    :return: result:
        Success with dict {"<listType>":[<objects>]} if succeed
        Fail if an error occurred
    """
    mapIdRes = {}
    page_size = 100
    firstBatch = yield LUNA_CLIENT.getList(listId, 1, page_size)

    if not firstBatch.success:
        error = Error.generateLunaError("get list '{}'".format(listId), firstBatch.body)
        return Result(error, error.getErrorDescription())
    listType = "persons" if 'persons' in firstBatch.body else "descriptors"
    count = firstBatch.body['count']

    for iterCount in range(200):

        argsList = [(listId, page, page_size) for page in range(1, (count + page_size - 1) // page_size + 1)]
        concurrentRes = yield pretendConcurrent(LUNA_CLIENT.getList, argsList, concurrency)

        for reply in concurrentRes:
            if not reply.success:
                error = Error.generateLunaError("get list '{}'".format(listId), reply.body)
                return Result(error, error.getErrorDescription())
            for obj in reply.body[listType]:
                if obj["id"] in mapIdRes:
                    continue
                mapIdRes[obj["id"]] = obj
            count = reply.body["count"]
        if len(mapIdRes) >= count:
            break
    else:
        error = Error.generateError(Error.FailedToGetObjectsFromLunaList,
                                    Error.FailedToGetObjectsFromLunaList.getErrorDescription().format(listId))
        return Result(error, error.getErrorDescription())
    result = list(mapIdRes.values())
    return Result(Error.Success, {listType: result})


def prepareFilters(filters: dict):
    """
    Merge pairs with range filters into ones with values pairs.

    :param filters: filters dict to prepare
    :return: merged filters dict
    """
    result_filters = {}
    for name in filters:
        if name.endswith('__gt') or name.endswith('__lt'):
            new_name = name[:-4]
            result_filters[new_name] = (filters.get(new_name+'__gt', None), filters.get(new_name+'__lt', None))
        else:
            result_filters[name] = filters[name]
    return result_filters


def markTaskAsInProgress(task: Task):
    """
    Functions to call when task starts

    :param task: a task
    :return: None
    """
    task.status = TaskStatus.IN_PROGRESS.value
    task.update_last_update()
    periodicUpdateTaskProgress(task, 2)
    periodicUpdateTaskStatus(task, 2)