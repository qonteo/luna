from tornado import gen

from errors.error import Error, Result
from common.tasks import Task

from app.common_objects import API_VERSION
from analytics.luna_api_request_with_retry import makeRequestToLunaApiWithRetry
from analytics.classes.clusterizer import Clusterizer
from analytics.workers.tasks_functions import flushFailedTask, markTaskAsInProgress
from analytics.common_objects import timer, logger, LUNA_CLIENT, ES_CLIENT as es


@timer.timerTor
@gen.coroutine
def cluster_worker(task: Task, concurrency = 10):
    """
    Function regulates the task process and occurred error process.

    :param task: task
    :param concurrency: count of synchronous functions to run
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    threshold = task.task.get('threshold')
    clusterizer = Clusterizer(task, concurrency, threshold)
    location = "/api/{}/analytics/tasks/{}".format(API_VERSION, task.id)
    markTaskAsInProgress(task)

    prepareRes = yield clusterizer.prepareData()
    if prepareRes.fail:
        logger.error("Task {} failed, reason: {}".format(task.id, prepareRes.description))
        yield flushFailedTask(task, prepareRes, location)
        return prepareRes

    if len(clusterizer.objectsIds) == 0:
        result = Result(Error.NoObjectsFound, 0)
        logger.error("Task {} failed, reason: {}".format(task.id, result.description))
        yield flushFailedTask(task, result, location)
        return result

    logger.debug("Object count for clusterization: {}, task {}".format(len(clusterizer.objectsIds), task.id))
    generateMatrixRes = yield clusterizer.fillMatrixOfSimilarity()

    if generateMatrixRes.fail:
        logger.error("Task {} failed, reason: {}".format(task.id, generateMatrixRes.description))
        yield flushFailedTask(task, generateMatrixRes, location)
        return generateMatrixRes

    clusters = clusterizer.generateClusters()
    clusters = clusterizer.generateObjectClusters(clusters)

    if clusterizer.deleteList:
        yield makeRequestToLunaApiWithRetry(LUNA_CLIENT.deleteList, 'delete list', clusterizer.listForMatching)

    logger.debug("Task {}, object count {}, cluster count {}".format(task.id, len(clusterizer.objectsIds),
                                                                     len(clusters)))
    task.success({"clusters": clusters, "total_clusters": len(clusters), "total_objects": len(clusterizer.objectsIds)})

    yield gen.sleep(2)
    yield es.markTaskDone(task, location)
    return Result(Error.Success, 0)
