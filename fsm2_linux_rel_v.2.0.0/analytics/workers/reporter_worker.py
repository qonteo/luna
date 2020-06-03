from itertools import chain

from tornado import gen

from analytics.classes.reporter import Reporter, ReporterObject
from analytics.common_objects import ES_CLIENT, LUNA_CLIENT, logger
from analytics.workers.tasks_functions import pretendConcurrent, flushFailedTask, markTaskAsInProgress
from app import API_VERSION
from common.tasks import Task, TaskType, TaskStatus
from errors.error import Error, Result


def getColor(similarity, colorMap):
    """
    Get color according to the similarity and color map.

    :param similarity: similarity
    :param colorMap: color->upper_similarity_boundary mapping
    :return: color
    """
    winner = 'gray'
    winner_delta = 1
    for color in colorMap:
        delta = similarity - colorMap[color]
        if 0 < delta < winner_delta:
            winner_delta = delta
            winner = color
    return winner


def commentDictMaker(obj, additionalFields):
    """
    Extract needed fields.

    :param obj: object to extract from
    :param additionalFields: field name list to extract
    :return: field->value mapping
    """
    result = {}
    for af in additionalFields:
        if af in obj:
            if af == 'similarity':
                result.update({af: round(obj[af], 3)})
            elif af == 'tags':
                if obj[af]:
                    result.update({af: '|'.join(obj[af])})
            else:
                result.update({af: obj[af]})
    return result


@gen.coroutine
def getListType(listId):
    """
    Find out Luna API list type.

    :param listId: list id
    :return: result:
        Success with <list type> if succeed
        Fail if an error occurred
    """
    reply = yield LUNA_CLIENT.getList(listId, 1, 0)
    if not reply.success:
        error = Error.generateLunaError("get list '{}' type".format(listId), reply.body)
        return Result(error, error.getErrorDescription())
    return Result(Error.Success, 'persons' if 'persons' in reply.body else 'descriptors')


@gen.coroutine
def getPersonDescriptorId(personId):
    """
    Get a first person descriptor.

    :param personId: person id
    :return: result:
        Success with {<person id>: <None> or <first person descriptor>} if succeed
        Fail if an error occurred
    """
    personRes = yield LUNA_CLIENT.getPerson(personId)
    if not personRes.success:
        error = Error.generateLunaError("get person '{}'".format(personId), personRes.body)
        return Result(error, error.getErrorDescription())
    if len(personRes.body['descriptors']):
        return Result(Error.Success, {personId: personRes.body['descriptors'][0]})
    return Result(Error.Success, {personId: None})


@gen.coroutine
def getGroupDescriptorId(groupId):
    """
    Get a first group descriptor.

    :param groupId: group id
    :return: result:
        Success with {<person id>: <first group descriptor>} if succeed
        Fail if an error occurred
    """
    groupRes = yield ES_CLIENT.getGroup(groupId)
    if not groupRes.success:
        return groupRes
    return Result(Error.Success, {groupId: groupRes.value['descriptors'][0]})


@gen.coroutine
def genCrossMatchDescriptorDict(crossMatchResult, referenceType, candidatesType, candidateIdSelector, concurrency=100):
    """
    Generate object->descriptor mapping.

    :param crossMatchResult: match list, match contains reference and candidate list
    :param referenceType: type of cross-match references
    :param candidatesType: type of cross-match candidates
    :param candidateIdSelector: "person_id" for persons, "id" for other
    :param concurrency: number of synchronous functions to run
    :return: tuple:
        makeDescriptorDict - object->descriptor mapping
        errors - occurred error list
    """
    references = [match['reference'] for match in crossMatchResult]
    candidates = [c[candidateIdSelector] for match in crossMatchResult for c in match['candidates']]

    makeDescriptorDict = {}
    errors = []
    for objects, objectType in ((references, referenceType), (candidates, candidatesType)):
        if objectType in ('persons', 'groups'):
            if objectType == 'persons':
                objectsRes = yield pretendConcurrent(getPersonDescriptorId, [[o] for o in objects], concurrency)
            else:  # objectType == 'groups'
                objectsRes = yield pretendConcurrent(getGroupDescriptorId, [[o] for o in objects], concurrency)
            for res in objectsRes:
                if res.success:
                    makeDescriptorDict.update(res.value)
                else:
                    errors.append(res)
        else:
            makeDescriptorDict.update({d: d for d in objects})

    return makeDescriptorDict, errors


@gen.coroutine
def genClusterizationDescriptorDict(clusterizationResult, objectType, concurrency):
    """
    Generate object->descriptor mapping.

    :param clusterizationResult: a cluster list, cluster is an object list
    :param objectType: the object type
    :param concurrency: number of synchronous functions to run
    :return: tuple:
        makeDescriptorDict - object->descriptor mapping
        errors - occurred error list
    """
    objects = list(chain(*clusterizationResult))

    errors = []
    if objectType == 'persons':
        makeDescriptorDict = {o['id']: o['descriptors'][0] for o in objects}
    elif objectType == 'groups':
        makeDescriptorDict = {}
        objectsRes = yield pretendConcurrent(getGroupDescriptorId, [[o['id']] for o in objects], concurrency)
        for res in objectsRes:
            if res.success:
                makeDescriptorDict.update(res.value)
            else:
                errors.append(res)
    else:
        makeDescriptorDict = {o['id']: o['id'] for o in objects}

    return makeDescriptorDict, errors


def prepareCrossMatchReportData(crossMatchResult, makeDescriptorDict, candidateIdSelector, objTypes, colorMap):
    """
    Prepare reporter object matrix from cross-match result.

    :param crossMatchResult:
    :param makeDescriptorDict: object->descriptor mapping
    :param candidateIdSelector: "person_id" for persons, "id" for other object types
    :param objTypes: tuple of object types: (<reference type>, <descriptor type>)
    :param colorMap: color->upper_similarity_boundary mapping
    :return: reporter object list list
    """
    additionalFields = [{
        "descriptors": ['last_update'],
        "persons": ['create_time', 'user_data'],
        "events": ['create_time', 'source', 'tags'],
        "groups": ['create_time', 'source', 'tags'],
    }[objType] for objType in objTypes]
    additionalFields[1].append('similarity')

    preparedCrossMatch = []
    for match in crossMatchResult:
        additionalData = commentDictMaker(match, additionalFields[0])
        preparedMatch = [ReporterObject(**{
            'object_id': match['reference'],
            'portrait_id': makeDescriptorDict.get(match['reference'], match['reference']),
            'color': 'white',
            'additional_fields': {k: str(additionalData.get(k, "")) for k in additionalFields[0]}
        })]
        for candidate in match['candidates']:
            additionalData = commentDictMaker(candidate, additionalFields[1])
            preparedMatch += [ReporterObject(**{
                'object_id': candidate[candidateIdSelector],
                'portrait_id': makeDescriptorDict.get(candidate[candidateIdSelector], candidate[candidateIdSelector]),
                'color': getColor(additionalData['similarity'], colorMap),
                'additional_fields': {k: str(additionalData[k]) for k in additionalFields[1] if k in additionalData}
            })]
        preparedCrossMatch.append(preparedMatch)
    return preparedCrossMatch


def prepareClusterizationReportData(clusterizationResult, makeDescriptorDict, objType):
    """
    Prepare reporter object matrix from clusterization result.

    :param clusterizationResult: cluster list
    :param makeDescriptorDict: object->descriptor mapping
    :param objType: type of objects in clusters
    :return: reporter object list list
    """
    additionalFields = {
        "descriptors": ['last_update'],
        "persons": ['user_data', 'create_time'],
        "events": ['create_time', 'source', 'tags', 'age', 'gender'],
        "groups": ['create_time', 'source', 'tags', 'age', 'gender'],
    }[objType]

    preparedClusterization = []
    for cluster in clusterizationResult:
        preparedRow = []
        for obj in cluster:
            additionalData = commentDictMaker(obj, additionalFields)
            preparedRow.append(ReporterObject(**{
                'object_id': obj['id'],
                'portrait_id': makeDescriptorDict.get(obj['id'], obj['id']),
                'color': 'white',
                'additional_fields': {k: str(additionalData.get(k, "")) for k in additionalFields}
            }))
        preparedClusterization.append(preparedRow)
    return preparedClusterization


@gen.coroutine
def cross_match_reporter_worker(task, doneTask, concurrency):
    """
    Prepare report object matrix from cross-match:
        get reference type
        get candidate type
        get cross-match result data
        make object-> descriptor mapping
        make color map
        make reporter object matrix

    :param task: task
    :param doneTask: done task
    :param concurrency: number of synchronous functions to run
    :return: result:
        Success with tuple:
            preparedCrossMatch - reporter object matrix
            types - tuple ("<reference type>", "<candidate type>")
        Fail if an error occurred
    """
    # get reference type
    referenceType = doneTask.task['references']['objects']
    if referenceType == 'luna_list':
        referenceTypeRes = yield getListType(doneTask.task['references']['filters']['list_id'])
        if referenceTypeRes.fail:
            return referenceTypeRes
        referenceType = referenceTypeRes.value

    # get candidate type
    candidatesTypeRes = yield getListType(doneTask.task['candidates']['list_id'])
    if candidatesTypeRes.fail:
        return candidatesTypeRes
    candidatesType = candidatesTypeRes.value

    # get data to prepare
    crossMatchResult = doneTask.result['success']

    if not len(crossMatchResult) or not len(crossMatchResult[0]['candidates']):
        return Result(Error.UnknownError, 0)
    candidateIdSelector = 'person_id' if candidatesType == 'persons' else 'id'

    # get object-> descriptor mapping
    makeDescriptorDict, errors = yield genCrossMatchDescriptorDict(
        crossMatchResult, referenceType, candidatesType, candidateIdSelector, concurrency
    )
    for error in errors:
        task.addError(error)
    task.progress = 0.2

    # get references and candidates types
    types = referenceType, candidatesType

    # make color map
    colorMap = {'green': 0.83, 'orange': 0.5, 'red': 0.3}
    if 'parameters' in task.task:
        colorMap = {**colorMap, **task.task['parameters'].get('colors_bounds', {})}

    # prepare data
    preparedCrossMatch = prepareCrossMatchReportData(crossMatchResult, makeDescriptorDict, candidateIdSelector, types, colorMap)
    return Result(Error.Success, (preparedCrossMatch, types))


@gen.coroutine
def clusterization_reporter_worker(task, doneTask, concurrency):
    """
    Prepare report object matrix from clusterization:
        get candidate type
        get clusters from doneTask
        make object->descriptor mapping
        make reporter object matrix

    :param task: task
    :param doneTask: done task
    :param concurrency: number of synchronous functions to run
    :return: result:
        Success with tuple:
            preparedClusterization - reporter object matrix
            objectType - cluster task objects' type
        Fail if an error occurred
    """
    # get candidate type
    objectType = doneTask.task['objects']
    if objectType == 'luna_list':
        objectTypeRes = yield getListType(doneTask.task['filters']['list_id'])
        if objectTypeRes.fail:
            return objectTypeRes
        objectType = objectTypeRes.value

    # get data to prepare
    clusterizationResult = doneTask.result['success']['clusters']

    # get object->descriptor mapping
    makeDescriptorDict, errors = yield genClusterizationDescriptorDict(
        clusterizationResult, objectType, concurrency
    )
    for error in errors:
        task.addError(error)
    task.progress = 0.2

    # prepare data
    preparedClusterization = prepareClusterizationReportData(clusterizationResult, makeDescriptorDict, objectType)
    return Result(Error.Success, (preparedClusterization, objectType))


@gen.coroutine
def reporter_worker(task: Task, concurrency=20):
    """
    Function to make report:
        get done task result
        prepare report object list list
        make report

    :param task: task
    :param concurrency: number of synchronous functions to run
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    reportLocation = "/api/{}/reports/{}".format(API_VERSION, task.id)
    location = "/api/{}/analytics/tasks/{}".format(API_VERSION, task.id)
    markTaskAsInProgress(task)

    logger.debug('Reporter task {}'.format(task.id))
    # get done task
    doneTaskId = task.task['task_id']
    doneTaskRes = yield ES_CLIENT.getDoneTask(doneTaskId)
    if doneTaskRes.fail:
        logger.error('Task {} failed, reason: {}'.format(task.id, doneTaskRes.description))
        yield flushFailedTask(task, doneTaskRes, location)
        return doneTaskRes
    doneTask = Task.generateTaskFromDict(doneTaskRes.value)

    if doneTask.status != TaskStatus.SUCCESS.value:
        msg = "Reporter got task {} with status '{}'".format(doneTask.id, doneTask.status)
        err = Error.generateError(Error.InconsistentInputDataError,
                                  Error.InconsistentInputDataError.getErrorDescription().format(msg))
        logger.error('Task {} failed, reason: {}'.format(task.id, msg))
        result = Result(err, msg)
        yield flushFailedTask(task, result, location)
        return result

    if doneTask.type == TaskType.CROSS_MATCHER:
        preparedDataRes = yield cross_match_reporter_worker(task, doneTask, concurrency)
        if preparedDataRes.fail:
            logger.error('Task {} failed, reason: {}'.format(task.id, preparedDataRes.description))
            yield flushFailedTask(task, preparedDataRes, location)
            return preparedDataRes
    elif doneTask.type == TaskType.CLUSTERIZATION:
        preparedDataRes = yield clusterization_reporter_worker(task, doneTask, concurrency)
        if preparedDataRes.fail:
            logger.error('Task {} failed, reason: {}'.format(task.id, preparedDataRes.description))
            yield flushFailedTask(task, preparedDataRes, location)
            return preparedDataRes
    else:
        result = Result(Error.NotImplementedError, 'Wrong resource task type for Reporter: "{}"'.format(doneTask.type))
        logger.error('Task {} failed, reason: {}'.format(task.id, result.description))
        yield flushFailedTask(task, result, location)
        return result

    preparedData, types = preparedDataRes.value
    reporter = Reporter(preparedData, task, 0.8, types)
    reporterRes = yield reporter.report(doneTask.type)
    if reporterRes.fail:
        logger.error('Task {} failed, reason: {}'.format(task.id, reporterRes.description))
        yield flushFailedTask(task, reporterRes, location)
        return reporterRes

    logger.debug('Task {} done'.format(task.id))
    task.success({"Location": reportLocation})
    yield gen.sleep(2)
    yield ES_CLIENT.markTaskDone(task, location)
    return Result(Error.Success, 0)
