from tornado import gen
from errors.error import Result, Error
from analytics.common_objects import LUNA_CLIENT, ES_CLIENT, logger, timer
from analytics.classes.list_linker import ListLinker
from analytics.classes.personalizator import Personalizator
from app.common_objects import API_VERSION
from analytics.workers.tasks_functions import flushFailedTask, periodicUpdateTaskProgress, \
    periodicUpdateTaskStatus, pretendConcurrent, getFullLunaList, prepareFilters, markTaskAsInProgress
from common.tasks import Task, TaskStatus


@gen.coroutine
def prepareList(task, listType='descriptors'):
    """
    Resolve list existence. Create if needed.

    :param task: task
    :param listType: list type to create if not exist
    :return: result:
        Success with list id if succeed
        Fail if an error occurred
    """
    listId = task.task.get('list_id', None)
    listDescription = task.task.get('list_data', "")
    if listId is None:
        lunaListRes = yield LUNA_CLIENT.createList(listType, listDescription)
        if not lunaListRes.success:
            return Result(Error.LunaRequestError, lunaListRes.body)
        listId = lunaListRes.body['list_id']
    else:
        listRes = yield LUNA_CLIENT.getList(listId, 1, 1)
        if not listRes.success:
            return Result(Error.LunaRequestError, listRes.body)
    return Result(Error.Success, listId)


@gen.coroutine
def checkPersonExistence(references: list, concurrency: int) -> dict:
    """
    Check whether a descriptor is already attached to a person.

    :param references: descriptor id iterator
    :return: descriptor->person mapping
    """
    descriptor8person = {}
    references = iter(references)

    @gen.coroutine
    def _worker():
        for descriptorId in references:
            reply = yield LUNA_CLIENT.getDescriptor(descriptorId)
            if reply.success and reply.body.get('person_id'):
                descriptor8person[descriptorId] = reply.body['person_id']
            elif not reply.success:
                err = Error.generateLunaError('get descriptor {}'.format(descriptorId), reply.body)
                logger.debug(err.getErrorDescription())
    yield [_worker() for i in range(concurrency)]
    return descriptor8person


@gen.coroutine
def makePersons(references: list, task: Task, weight, concurrency=3):
    """
    Make persons from descriptor list list.

    :param references: descriptor list list
    :param task: task to update progress
    :param weight: weight of this task step
    :param concurrency: number of synchronous functions to run
    :return: personalizator.personalize result
    """
    personalizator = Personalizator(references, task, weight)
    personalizatorRes = yield personalizator.personalize(concurrency)
    return personalizatorRes


@gen.coroutine
def makeLinks(listId: str, listType: str, references: list, task: Task, weight: float, concurrency=3):
    """
    Make links - attach objects (descriptors or persons) to the Luna API list with corresponding type.

    :param listId: Luna API list id to attach to
    :param listType: type of Luna API list and objects also
    :param references: descriptors/persons list
    :param task: task to update progress
    :param weight: weight of this step
    :param concurrency: number of synchronous functions to run
    :return: linker.link result
    """
    linker = ListLinker(listId, listType, references, task, weight)
    linkerRes = yield linker.link(concurrency)
    return linkerRes


@gen.coroutine
def linkEventsToDescriptorsList(task: Task, concurrency=3):
    """
    Linker function for linking events with Luna API descriptors list.

    :param task: task
    :param concurrency: number of synchronous functions to run
    :return: result:
        Success with {'succeed': <success count>, 'failed': <fail count>} if succeed
        Fail if an error occurred
    """
    filters = prepareFilters(task.task['filters'])
    referencesRes = yield ES_CLIENT.getAll(ES_CLIENT.SearchEvent(**filters), source=['descriptor_id'])
    if referencesRes.fail:
        return referencesRes
    references = [e['descriptor_id'] for e in referencesRes.value['hits']]

    listDescriptorsRes = yield prepareList(task, 'descriptors')
    if listDescriptorsRes.fail:
        return listDescriptorsRes
    listDescriptors = listDescriptorsRes.value
    task.task['list_id'] = listDescriptors

    linkerRes = yield makeLinks(listDescriptors, 'descriptors', references, task, 0.2, concurrency)
    if linkerRes.fail:
        return linkerRes

    eventsToUpdate = {descriptorId.value: listDescriptors for descriptorId in linkerRes.value if descriptorId.success}

    for descriptorId in linkerRes.value:
        if descriptorId.fail:
            task.addError(Error.generateError(
                Error.LinkDescriptorError,
                Error.LinkDescriptorError.getErrorDescription().format(descriptorId, listDescriptors))
            )

    updateRes = yield pretendConcurrent(ES_CLIENT.addListDescriptorsToEvent, eventsToUpdate.items(), concurrency)
    if any(res.fail for res in updateRes):
        logger.debug("Cannot update descriptors list in events for task \"{}\"".format(task.id))

    successCount = len([0 for linkRes in linkerRes.value if linkRes.success])
    failCount = len(linkerRes.value) - successCount
    return Result(Error.Success, {'succeed': successCount, 'failed': failCount})


@gen.coroutine
def linkEventsToPersonsList(task: Task, concurrency=3):
    """
    Linker function for linking events with Luna API persons list.

    :param task: task
    :param concurrency: number of synchronous functions to run
    :return: result:
        Success with {'succeed': <success count>, 'failed': <fail count>} if succeed
        Fail if an error occurred
    """
    # get events
    filters = prepareFilters(task.task['filters'])
    referencesRes = yield ES_CLIENT.getAll(ES_CLIENT.SearchEvent(**filters), source=['descriptor_id', 'person_id'])
    if referencesRes.fail:
        return referencesRes
    references = [
        {'descriptors': [e['descriptor_id']], 'event_id': e['descriptor_id']}
        for e in referencesRes.value['hits']
        if e['person_id'] is None
    ]

    # find attached persons
    descriptor8person = yield checkPersonExistence([d for r in references for d in r['descriptors']], concurrency)
    descriptorsWithPersons = set(descriptor8person)
    references = [r for r in references if r['descriptors'][0] not in descriptorsWithPersons]

    # get already existent persons
    event8person = {
        e['descriptor_id']: e['person_id']
        for e in referencesRes.value['hits']
        if e['person_id'] is not None
    }
    event8person.update(descriptor8person)
    persons = set(event8person.values())

    allCount = len(references) + len(persons)

    # create list or get it from the task
    listPersonsRes = yield prepareList(task, 'persons')
    if listPersonsRes.fail:
        return listPersonsRes
    listPersons = listPersonsRes.value
    task.task['list_id'] = listPersons

    # create persons from descriptors
    personalizatorRes = yield makePersons(references, task, 0.2)
    if personalizatorRes.fail:
        # no descriptors were attached (logical error)
        return personalizatorRes

    # update events in es
    eventsToUpdate = {
        **{res.value['event_id']: res.value['person_id'] for res in personalizatorRes.value if res.success},
        **descriptor8person
    }
    event8person.update(eventsToUpdate)
    updateRes = yield pretendConcurrent(ES_CLIENT.updatePersonInEvent, eventsToUpdate.items(), concurrency)
    if any(res.fail for res in updateRes):
        logger.debug("Cannot update persons in events for task \"{}\"".format(task.id))

    persons.update(set(eventsToUpdate.values()))

    # link persons with list
    linkerRes = yield makeLinks(listPersons, 'persons', list(persons), task, 0.2, concurrency)
    if linkerRes.fail:
        # no persons were attached (logical error)
        return linkerRes

    # update list in succeeded events
    eventsToUpdate = {
        eventId: listPersons
        for res in linkerRes.value
        if res.success
        for eventId in event8person
        if event8person[eventId] == res.value
    }

    updateRes = yield pretendConcurrent(ES_CLIENT.addListPersonsToEvent, eventsToUpdate.items(), concurrency)
    if any(res.fail for res in updateRes):
        logger.debug("Cannot update person lists in events for task \"{}\"".format(task.id))

    successCount = len(eventsToUpdate) - len([res for res in updateRes if res.fail])
    failCount = allCount - successCount
    return Result(Error.Success, {'succeed': successCount, 'failed': failCount})


@gen.coroutine
def linkGroupsToPersonsList(task: Task, concurrency):
    """
    Linker function for linking groups with Luna API persons list.

    :param task: task
    :param concurrency: number of synchronous functions to run
    :return: result:
        Success with {'succeed': <success count>, 'failed': <fail count>} if succeed
        Fail if an error occurred
    """
    # get groups without person_id
    filters = prepareFilters(task.task['filters'])
    referencesRes = yield ES_CLIENT.getAll(ES_CLIENT.SearchGroup(**filters), source=['id', 'descriptors', 'person_id'])
    references = [
        {'descriptors': g['descriptors'], 'group_id': g['id']}
        for g in referencesRes.value['hits']
        if g['person_id'] is None
    ]

    # find inconsistent groups
    descriptor8person = yield checkPersonExistence([d for r in references for d in r['descriptors']], concurrency)
    inconsistentGroups = {}
    for groupNum in range(len(references)):
        for descriptor_id in references[groupNum]['descriptors']:
            if descriptor_id in descriptor8person:
                inconsistentGroups[groupNum] = descriptor_id, descriptor8person[descriptor_id]
                break

    # add inconsistent errors
    for groupNum in inconsistentGroups:
        err = Error.generateError(
            Error.InconsistentInputDataError, Error.InconsistentInputDataError.getErrorDescription().format((
                "in group '{}' descriptor '{}' was attached to person '{}', "
                "although the group has empty person_id field"
            ).format(references[groupNum]['group_id'], *inconsistentGroups[groupNum])))
        task.addError(Result(err, 0))

    # remove inconsistent groups from references
    for groupNum in sorted(list(inconsistentGroups), reverse=True):
        references.pop(groupNum)

    # get groups with person_id
    person8group = {
        g['person_id']: g['id']
        for g in referencesRes.value['hits']
        if g['person_id'] is not None
    }

    allCount = len(references) + len(person8group)

    # get list
    listPersonsRes = yield prepareList(task, 'persons')
    if listPersonsRes.fail:
        return listPersonsRes
    listPersons = listPersonsRes.value
    task.task['list_id'] = listPersons

    # make persons from groups without persons
    personalizatorRes = yield makePersons(references, task, 0.2, concurrency)
    if personalizatorRes.fail:
        # no descriptors were attached (logical error)
        return personalizatorRes

    # update persons in groups
    groupsToUpdate = {res.value['group_id']: res.value['person_id'] for res in personalizatorRes.value if res.success}
    person8group.update({v: k for k, v in groupsToUpdate.items()})
    updateRes = yield pretendConcurrent(ES_CLIENT.updatePersonInGroup, groupsToUpdate.items(), concurrency)
    if any(res.fail for res in updateRes):
        logger.debug("Cannot update persons in events for task \"{}\"".format(task.id))

    # link result persons
    persons = list(person8group.keys())
    linkerRes = yield makeLinks(listPersons, 'persons', persons, task, 0.2, concurrency)
    if linkerRes.fail:
        # no persons were attached (logical error)
        return linkerRes

    # update person list in groups
    groupsToUpdate = {person8group[res.value]: listPersons for res in linkerRes.value if res.success}
    updateRes = yield pretendConcurrent(ES_CLIENT.addListPersonsToGroup, groupsToUpdate.items(), concurrency)
    if any(res.fail for res in updateRes):
        logger.debug("Cannot update person lists in groups for task \"{}\"".format(task.id))

    successCount = len(groupsToUpdate) - len([res for res in updateRes if res.fail])
    failCount = allCount - successCount
    return Result(Error.Success, {'succeed': successCount, 'failed': failCount})


@gen.coroutine
def linkLunaListToDescriptorsList(task: Task, concurrency):
    """
    Linker function for linking descriptors or persons from Luna API list with Luna API descriptors list.

    :param task: task
    :param concurrency: number of synchronous functions to run
    :return: result:
        Success with {'succeed': <success count>, 'failed': <fail count>} if succeed
        Fail if an error occurred
    """
    listSource = task.task['filters']['list_id']
    listRes = yield getFullLunaList(listSource, concurrency)
    if listRes.fail:
        return listRes
    listType = next(iter(listRes.value.keys()))
    if listType == "descriptors":
        descriptors = [d['id'] for d in listRes.value[listType]]
    else:
        descriptors = [d for p in listRes.value[listType] for d in p['descriptors']]
        # descriptor8person = {d: p['id'] for p in listRes.value[listType] for d in p['descriptors']}

    allCount = len(descriptors)

    task.progress = 0.2

    listDescriptorsRes = yield prepareList(task, 'descriptors')
    if listDescriptorsRes.fail:
        return listDescriptorsRes
    listDescriptors = listDescriptorsRes.value
    task.task['list_id'] = listDescriptors

    linkerRes = yield makeLinks(listDescriptors, 'descriptors', descriptors, task, 0.8, concurrency)
    if linkerRes.fail:
        return linkerRes
    successCount = len([res for res in linkerRes.value if res.success])
    failCount = allCount - successCount
    return Result(Error.Success, {'succeed': successCount, 'failed': failCount})


@gen.coroutine
def linkLunaListToPersonsList(task: Task, concurrency):
    """
    Linker function for linking descriptors or persons from Luna API list with Luna API persons list.

    :param task: task
    :param concurrency: number of synchronous functions to run
    :return: result:
        Success with {'succeed': <success count>, 'failed': <fail count>} if succeed
        Fail if an error occurred
    """
    listSource = task.task['filters']['list_id']
    listRes = yield getFullLunaList(listSource, concurrency)
    if listRes.fail:
        return listRes
    listType = next(iter(listRes.value.keys()))

    task.progress = 0.2

    if listType == "persons":
        persons = [d['id'] for d in listRes.value[listType]]
        percent = 0
        allCount = len(persons)
    else:
        persons = [d['person_id'] for d in listRes.value[listType] if d['person_id'] is not None]
        descriptors = [{"descriptors": [d['id']]} for d in listRes.value[listType] if d['person_id'] is None]

        allCount = len(persons) + len(descriptors)
        percent = 1/2 * len(descriptors) / (len(descriptors) + len(persons))

        personalizatorRes = yield makePersons(descriptors, task, percent, concurrency)
        if personalizatorRes.fail:
            return personalizatorRes
        # errors = [res for res in persRes.value if res.fail]
        persons += [res.value['person_id'] for res in personalizatorRes.value if res.success]

    listPersonsRes = yield prepareList(task, 'persons')
    if listPersonsRes.fail:
        return listPersonsRes
    listPersons = listPersonsRes.value
    task.task['list_id'] = listPersons

    linkerRes = yield makeLinks(listPersons, 'persons', persons, task, 0.8 - percent, concurrency)
    if linkerRes.fail:
        return linkerRes
    successCount = len([res for res in linkerRes.value if res.success])
    failCount = allCount - successCount
    return Result(Error.Success, {'succeed': successCount, 'failed': failCount})


@timer.timerTor
@gen.coroutine
def rootLinker(task: Task, concurrency=3):
    """
    Function to validate task, choose linker function based on the object and Luna API list types and run it.

    :param task: task
    :param concurrency: number of synchronous functions to run
    :return: result:
        Success with {'succeed': <success count>, 'failed': <fail count>} if succeed
        Fail if an error occurred
    """
    location = "/api/{}/analytics/tasks/{}".format(API_VERSION, task.id)
    taskObject = task.task['object']
    listType = task.task['list_type']
    markTaskAsInProgress(task)

    functionToCall = {
        ('events', 'descriptors'):    linkEventsToDescriptorsList,
        ('events', 'persons'):        linkEventsToPersonsList,
        ('groups', 'persons'):        linkGroupsToPersonsList,
        ('luna_list', 'descriptors'): linkLunaListToDescriptorsList,
        ('luna_list', 'persons'):     linkLunaListToPersonsList,
    }.get((taskObject, listType), None)
    # validations
    if functionToCall is None:
        message = "Task {} failed, reason: Wrong linker task target '{}'->'{}'".format(task.id, taskObject, listType)
        logger.error(message)
        res = Result(Error.UnknownTaskType, message)
        yield flushFailedTask(task, res, location)
        return res
    if taskObject == 'luna_list':
        filterList = task.task['filters']['list_id']
        listRes = yield LUNA_CLIENT.getList(filterList)
        if not listRes.success:
            res = Result(Error.generateLunaError("Filter 'list_id': '{}'".format(filterList), listRes.body), 0)
            logger.error('Task {} failed, reason: {}'.format(task.id, res.description))
            yield flushFailedTask(task, res, location)
            return res
    targetList = task.task.get('list_id', None)
    if targetList is not None:
        listRes = yield LUNA_CLIENT.getList(targetList)
        if not listRes.success:
            res = Result(Error.generateLunaError("Result 'list_id': '{}'".format(targetList), listRes.body), 0)
            logger.error('Task {} failed, reason: {}'.format(task.id, res.description))
            yield flushFailedTask(task, res, location)
            return res

    # linker work
    result = yield functionToCall(task, concurrency)

    if not result.success:
        logger.error('Task {} failed, reason: {}'.format(task.id, result.description))
        yield flushFailedTask(task, result, location)
        return result
    logger.debug('Task {} done'.format(task.id))
    task.success(result.value)

    yield gen.sleep(2)  #: wait a synchronization of schards in ES
    yield ES_CLIENT.markTaskDone(task, location)
    return result
