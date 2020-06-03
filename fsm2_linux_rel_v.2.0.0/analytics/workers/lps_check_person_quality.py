from tornado import gen
from errors.error import Error, Result
from analytics.common_objects import logger, LUNA_CLIENT, ES_CLIENT
from analytics.common_objects import timer
from common.tasks import Task, TaskStatus
from analytics.workers.tasks_functions import flushFailedTask, periodicUpdateTaskProgress, periodicUpdateTaskStatus, \
    markTaskAsInProgress
from analytics.luna_api_request_with_retry import makeRequestToLunaApiWithRetry
from analytics.classes.matcher import Matcher
from analytics.classes.list_linker import ListLinker
from app.common_objects import API_VERSION


def getStats(references, other, results, top_n):
    """
    Calculate the result statistics.

    :param references: descriptor->person mapping
    :param other:
    :param results: match results
    :param top_n: number of results to store
    :return: hit top n list
    """
    counter = []
    for d in results:
        result = results[d][1:]
        expectedPerson = references[d]
        for i in range(len(result)):
            if other[result[i]] == expectedPerson:
                while len(counter) <= i:
                    counter += [0]
                counter[i] += 1
                break

    for i in range(len(counter) - 1):
        counter[i + 1] += counter[i]

    counter = [c / len(results) if len(results) else 0 for c in counter]
    while len(counter) < top_n:
        counter.append(counter[-1])
    return counter


@gen.coroutine
def generateList():
    replyRes = yield makeRequestToLunaApiWithRetry(LUNA_CLIENT.createList,
                                                   error_msg = "generate descriptors list",
                                                   listType = "descriptors",
                                                   listData = "list for person quality check")
    return replyRes


@gen.coroutine
def getPersons(listPersons):
    """
    Get persons, filter out one-descriptor persons,

    :param listPersons:
    :return: result:
        Success with tuple:
            references - descriptor->person mapping for several-descriptors person
            candidates - full descriptor->person mapping
        Fail if an error occurred
    """
    firstBatchRes = yield makeRequestToLunaApiWithRetry(LUNA_CLIENT.getList, "get list", listId = listPersons,
                                                        page = 1, pageSize = 100)
    if firstBatchRes.fail:
        return firstBatchRes
    if 'persons' not in firstBatchRes.value:
        error = Error.generateLunaError("empty list", firstBatchRes.value)
        logger.error("empty list")
        return Result(error, firstBatchRes.value)

    persons = firstBatchRes.value['persons']
    for i in range(2, (firstBatchRes.value['count'] + 100 - 1) // 100 + 1):
        batchRes = yield makeRequestToLunaApiWithRetry(LUNA_CLIENT.getList, "get list", listId = listPersons,
                                                       page = i, pageSize = 100)
        if batchRes.fail:
            return batchRes
        batch = batchRes.value
        persons += batch['persons']
    personsWithSeveralDescriptors = [person for person in persons if len(person['descriptors']) > 1]

    references = {descriptor: person['id']
                  for person in personsWithSeveralDescriptors for descriptor in person['descriptors']}
    candidates = {descriptor: person['id'] for person in persons for descriptor in person['descriptors']}
    return Result(Error.Success, (references, candidates))


@gen.coroutine
def makeLink(candidates, listDescriptors, concurrency, task):
    """
    Link candidates descriptors to the Luna API descriptors list.

    :param candidates: candidates descriptor->person mapping to link
    :param listDescriptors: the Luna API descriptors list
    :param concurrency: number of synchronous functions to run
    :param task: task to update progress
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    linker = ListLinker(listDescriptors, 'descriptors', list(candidates), task, 0.5)
    linkResult = yield linker.link(concurrency)
    if not linkResult.success or any(res.fail for res in linkResult.value):
        yield LUNA_CLIENT.deleteList(listDescriptors)
        return Result(Error.LinkDescriptorsError, linkResult.value)
    task.progress = 0.5
    return Result(Error.Success, 0)


@gen.coroutine
def makeMatches(references, listDescriptors, concurrency, matchLimit, task: Task):
    """
    Match references with the Luna API descriptors list.

    :param references: references descriptor->person mapping to match
    :param listDescriptors: the Luna API candidates list to match with
    :param concurrency: number of synchronous functions to run
    :param matchLimit: matcher limit (top_n + 1)
    :param task: task to update progress
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    matcher = Matcher(listDescriptors, list(references), matchLimit, task, 0.5)
    match_result = yield matcher.match(2 * concurrency)
    return match_result


@timer.timerTor
@gen.coroutine
def calculateHitTopNListPersonProbability(task: Task, concurrency = 10):
    """
    Calculate hit top n probability:
        get references to match and candidates to match to
        create a Luna API descriptors list
        link the candidates to the Luna API descriptors list
        match references with the Luna API descriptors list
        calculate statistics

    :param task: task
    :param concurrency: number of synchronous functions to run
    :return: result:
        Success with <hit top n result list> if succeed
        Fail if an error occurred
    """
    location = "/api/{}/analytics/tasks/{}".format(API_VERSION, task.id)
    top_n = task.task["top_n"]
    markTaskAsInProgress(task)

    listPersons = task.task["list_id"]
    personResult = yield getPersons(listPersons)
    if not personResult.success:
        logger.error('Task {} failed, reason: {}'.format(task.id, personResult.description))
        yield flushFailedTask(task, personResult, location)
        return personResult

    # both are descriptor->person mappings
    references, candidates = personResult.value

    listCandidatesResponse = yield generateList()
    if not listCandidatesResponse.success:
        logger.error('Task {} failed, reason: {}'.format(task.id, listCandidatesResponse.description))
        yield flushFailedTask(task, listCandidatesResponse, location)
        return listCandidatesResponse
    listCandidates = listCandidatesResponse.value["list_id"]

    linkResults = yield makeLink(candidates, listCandidates, concurrency, task)
    if linkResults.fail:
        yield makeRequestToLunaApiWithRetry(LUNA_CLIENT.deleteList, 'delete list', listCandidates)
        logger.error('Task {} failed, reason: {}'.format(task.id, linkResults.description))
        yield flushFailedTask(task, linkResults, location)
        return linkResults

    resultsRes = yield makeMatches(references, listCandidates, concurrency, top_n + 1, task)
    yield makeRequestToLunaApiWithRetry(LUNA_CLIENT.deleteList, 'delete list', listCandidates)
    if resultsRes.fail:
        logger.error('Task {} failed, reason: {}'.format(task.id, resultsRes.description))
        yield flushFailedTask(task, resultsRes, location)
        return resultsRes

    results = {k: [d['id'] for d in v] for k, v in resultsRes.value.items()}

    counter = getStats(references, candidates, results, top_n)
    logger.debug('Task {} done'.format(task.id))
    task.success({"tops": counter, "total": len(counter)})

    yield gen.sleep(2)  #: wait a synchronization of schards in ES
    yield ES_CLIENT.markTaskDone(task, location)
    return Result(Error.Success, counter)
