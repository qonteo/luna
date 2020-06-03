from tornado import gen
from functools import cmp_to_key

from app.common_objects import API_VERSION
from common.tasks import Task, TaskStatus
from configs import config
from errors.error import Result, Error
from analytics.classes.matcher import Matcher
from common.majority_voting import majorityVoting
from analytics.common_objects import LUNA_CLIENT, ES_CLIENT, timer, logger
from analytics.workers.tasks_functions import periodicUpdateTaskProgress, periodicUpdateTaskStatus, prepareFilters, \
    flushFailedTask, getFullLunaList, markTaskAsInProgress


@gen.coroutine
def _getReferences(referencesDict):
    """
    Get references list based on

    :param referencesDict: task["references"] dict
    :return: result:
        Success with tuple of three variables:
            result - {"persons": []} or {"descriptors": []}
            referenceRenameFunc - get id of object by id of descriptor/person
            additionalDataGetter - {"<object_id>": <additional_data_dictionary>}
        Fail if an error occurred
    """
    result = {'descriptors': [], 'persons': []}
    if referencesDict['objects'] == 'luna_list':
        listId = referencesDict['filters']['list_id']
        listRes = yield getFullLunaList(listId, 10)
        if not listRes.success:
            return listRes
        if 'descriptors' in listRes.value:
            listType = 'descriptors'
            additionalDataDict = {r['id']: {"last_update": r['last_update']} for r in listRes.value[listType]}
        else:
            listType = 'persons'
            additionalDataDict = {
                r['id']: {"user_data": r['user_data'], "create_time": r['create_time']}
                for r in listRes.value[listType]
            }

        result[listType] += [r['id'] for r in listRes.value[listType]]
        referenceRenameFunc = lambda x: x
    elif referencesDict['objects'] == 'events':
        referencesRes = yield ES_CLIENT.getAll(ES_CLIENT.SearchEvent(**prepareFilters(referencesDict['filters'])),
                                               ['descriptor_id', 'source', 'create_time', 'tags'])
        if referencesRes.fail:
            return referencesRes
        result['descriptors'] += [e['descriptor_id'] for e in referencesRes.value['hits'] if e['descriptor_id'] is not None]
        referenceRenameFunc = lambda x: x
        additionalDataDict = {
            e['descriptor_id']: {"source": e['source'], "create_time": e['create_time'], "tags": e['tags']}
            for e in referencesRes.value['hits']
            if e['descriptor_id'] is not None
        }
    elif referencesDict['objects'] == 'groups':
        referencesRes = yield ES_CLIENT.getAll(ES_CLIENT.SearchGroup(**prepareFilters(referencesDict['filters'])),
                                               ['id', 'descriptors', 'source', 'create_time', 'tags'])
        if referencesRes.fail:
            return referencesRes
        descriptor8group = {}
        for g in referencesRes.value['hits']:
            descriptor8group.update({d: g['id'] for d in g['descriptors']})
            result['descriptors'] += g['descriptors']
        referenceRenameFunc = lambda r: descriptor8group[r]
        additionalDataDict = {
            g['id']: {"source": g['source'], "create_time": g['create_time'], "tags": g['tags']}
            for g in referencesRes.value['hits']
        }
    else:
        msg = Error.BadTypeOfFieldInJSON.getErrorDescription().format("references.objects",
                                                                      "one of 'luna_list','events','groups'")
        error = Error.generateError(Error.BadTypeOfFieldInJSON, msg)
        return Result(error, msg)
    additionalDataGetter = additionalDataDict.get
    return Result(Error.Success, (result, referenceRenameFunc, additionalDataGetter))


@gen.coroutine
def prepare(task):
    """
    Check candidate Luna API list existence and get references.

    :param task: task
    :return: result:
        Success with tuple of three variables:
            result - {"persons": []} or {"descriptors": []}
            referenceRenameFunc - get id of object by id of descriptor/person
            additionalDataGetter - {"<object_id>": <additional_data_dictionary>}
        Fail if an error occurred
    """
    referencesDict = task.task['references']
    candidatesList = task.task['candidates']['list_id']
    listRes = yield LUNA_CLIENT.getList(candidatesList, 1, 1)
    if not listRes.success:
        res = Result(Error.generateLunaError("get references list '{}'".format(candidatesList), listRes.body),
                     listRes.body)
        return res

    referencesRes = yield _getReferences(referencesDict)
    return referencesRes


@gen.coroutine
def make_result(candidatesList, matchResult, originalNameGetter, additionalDataGetter, task):
    """
    Sort match results, add additional references' data, cut first 40k.

    :param candidatesList: candidate list id
    :param matchResult: match list
    :param originalNameGetter: Luna API object id (persons or descriptors) -> real object id (events, groups,
        descriptors or persons) mapping
    :param additionalDataGetter: real object id (events, groups, descriptors or persons) -> additional data dict mapping
    :param task: task
    :return: result:
        Success with cross-match result dict
        Fail if an error occurred
    """
    threshold = task.task.get('threshold', 0)

    preFinal = {}  #: final results
    resultForVote = {}  #: doubles to resolve
    for refId in matchResult:
        newRefId = originalNameGetter(refId)
        if newRefId in preFinal:
            resultForVote[newRefId] = [matchResult[refId]]
            resultForVote[newRefId].append(preFinal.pop(newRefId))
        elif newRefId in resultForVote:
            resultForVote[newRefId].append(matchResult[refId])
        else:
            preFinal[newRefId] = matchResult[refId]

    for newRefId in resultForVote:
        data = [
            {"list_id": candidatesList, "candidates": candidates, "score": 1}
            for candidates in resultForVote[newRefId]
        ]
        res = majorityVoting(data)
        preFinal[newRefId] = [vote['candidate'] for vote in res]

    @cmp_to_key
    def lexicographicCMP(x, y):
        """
        Lexicographic sort function with CMP to Key decorator.

        :param x: first object to compare
        :param y: second object to compare
        :return: positive if x > y, negative if x < y, zero if x == y
        """
        for i in range(min((len(x['candidates']), len(y['candidates'])))):
            if x['candidates'][i]['similarity'] == y['candidates'][i]['similarity']:
                continue
            return x['candidates'][i]['similarity'] - y['candidates'][i]['similarity']
        return len(y['candidates']) - len(x['candidates'])

    # sort, cut threshold, slice first 40k due to elasticsearch database
    final = sorted([
        {
            "reference": reference,
            "candidates": candidates[:config.CANDIDATES_TO_STORE],
            **additionalDataGetter(reference)
        }
        for reference, candidates in preFinal.items()
        if any(c['similarity'] > threshold for c in candidates)
    ], key=lexicographicCMP, reverse=True)[:40000]
    return Result(Error.Success, final)


@timer.timerTor
@gen.coroutine
def crossMatch(task: Task, concurrency=3):
    """
    Cross-match worker function. Start task, validate input, complete task.

    :param task: task
    :param concurrency: the synchronous functions number
    :return: result:
        Success with cross-match result dict if succeed
        Fail if an error occurred
    """
    location = "/api/{}/analytics/tasks/{}".format(API_VERSION, task.id)
    limit = task.task.get('limit', None)
    candidatesList = task.task['candidates']['list_id']

    markTaskAsInProgress(task)

    preparation = yield prepare(task)
    if not preparation.success:
        logger.error("Task {} failed, reason: {}".format(task.id, preparation.description))
        flushFailedTask(task, preparation, location)
        return preparation
    references, originalNameGetter, additionalDataGetter = preparation.value

    # match
    if references['persons'] and references['descriptors']:
        raise RuntimeError(str(task.json) + str(references))

    refType = 'persons' if references['persons'] else 'descriptors'
    matcher = Matcher(candidatesList, references[refType], limit, task, 0.8, referencesType=refType)
    matchRes = yield matcher.match(concurrency)
    if matchRes.fail:
        logger.error('Task {} failed, reason: {}'.format(task.id, matchRes.description))
        flushFailedTask(task, matchRes, location)
        return matchRes
    matchResult = matchRes.value

    finalRes = yield make_result(candidatesList, matchResult, originalNameGetter, additionalDataGetter, task)
    if finalRes.fail:
        logger.error("Task {} failed, reason: {}".format(task.id, preparation.description))
        flushFailedTask(task, finalRes, location)
        return finalRes
    final = finalRes.value

    task.progress = 1
    logger.debug('Task {} done'.format(task.id))
    task.success(final)

    yield gen.sleep(2)  #: wait a synchronization of schards in ES
    yield ES_CLIENT.markTaskDone(task, location)
    return Result(Error.Success, final)
