import ujson as json
import uuid
from functools import wraps
from time import time

from tornado import gen
from tornado import locks

from app.common_objects import logger
from app.common_objects import timer
from app.enums import *
from app.queue.group_update_consumer import GROUP_UPDATE_QUEUE, GROUP_CLOSE_QUEUE, GROUP_UPDATE_GROUP_ID
from app.group_search_aggregators import top3Aggregator, majorityVotingAggreagator
from common.helpers import getNowTimestampMillis
from configs.config import GENDER_THRESHOLD
from errors.error import ErrorInfo
from errors.error import Result, Error

lock = locks.Lock()


def lockGuard(wrapFunc):
    """
    Lock group storage decorator.

    :param wrapFunc: function for decoration
    :return: wrapped function
    """
    @wraps(wrapFunc)
    @gen.coroutine
    def wrap(*func_args, **func_kwargs):
        with (yield lock.acquire()):
            res = yield wrapFunc(*func_args, **func_kwargs)
            return res

    return wrap


def getGenderWithMaxDeviation(group):
    """
    Get maximum deviate gender.

    :param group: group to aggregate gender from
    :return: maximum deviate gender
    """
    deviation = 0
    res = mean = GENDER_THRESHOLD
    for event in group.events:
        gender = event.extract["attributes"]["gender"]
        dev = abs(mean - gender)
        if dev > deviation:
            deviation = dev
            res = gender
    return res


def updateGroupFields(group, newEvent, groupingPolicy):
    """
    Recalculate age, gender and search result for group.

    :param group: group
    :param newEvent: new event for group
    :param groupingPolicy: group policy
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    group.events.append(newEvent)
    group.tags = list(set(newEvent.tags + group.tags))

    if "attributes" in newEvent.extract:
        group.attributes = GroupAttributes()
        if groupingPolicy.gender == GenderChoice.MEAN:
            group.attributes.gender = getAverageAttributeValue(group, "gender")
        elif groupingPolicy.gender == GenderChoice.MAX_DEVIATION:
            group.attributes.gender = getGenderWithMaxDeviation(group)
        else:
            group.attributes.gender = getGenderWithMaxDeviation(group)

        if groupingPolicy.age == AgeChoice.MEAN:
            group.attributes.age = int(getAverageAttributeValue(group, "age"))
        else:
            return Result(Error.UnknownError, "unknown aggregator")

    if groupingPolicy.search == SearchChoice.MAJORITY_VOTING:
        group.search = majorityVotingAggreagator(group)
    else:
        group.search = top3Aggregator(group)
    return Result(Error.Success, 0)


def getAverageAttributeValue(group, field: str):
    """
    Returns average value of age or gender for group

    :param group: group
    :param field: "gender" or "age"
    :return: average value
    """
    res = 0
    for event in group.events:
        res += event.extract["attributes"][field]
    return res / len(group.events)


class GroupAttributes:
    """
    Group attributes structure.
    """
    def __init__(self):
        self.gender = None
        self.age = None


class Group:
    """
    Group class.

    Attributes:
        id (UUID4): a unique group id
        person_id (UUID4): created person id
        descriptors (list of UUID4): event id (=descriptor) list
        source (str): the events’ source in group
        ttl (int): group time to live
        external_tracks_id (list): external track id list
        handler_id (UUID4): group handler id
        processed (bool): if group is closed
        create_time (timestamp): group create time
        last_update (timestamp): group last update time, it equals group close time if group is closed
        search (list): the result of search extracted descriptor by recent events in group
        events (list of Event): group event list
        attributes (dict): the aggregated events’ attributes.
        group_policy (GroupPolicy): processing group policy
        persons_lists (list of UUID4): Luna API person lists the created person is in
        error (NoneType): a error if occurred
        tags (list): the events’ tags list
    """
    def __init__(self, groupPolicy, source = None, externalId = None):
        self.id = str(uuid.uuid4())
        self.person_id = None
        self.descriptors = []
        self.source = source
        self.ttl = groupPolicy.ttl
        self.external_tracks_id = []
        self.handler_id = None

        if externalId is not None:
            self.external_tracks_id.append(externalId)
        self.processed = False
        self.create_time = getNowTimestampMillis()
        self.last_update = getNowTimestampMillis()
        self.search = None
        self.events = []
        self.attributes = None
        self.group_policy = groupPolicy
        self.persons_lists = []
        self.error = None
        self.tags = []

    def setError(self, error: ErrorInfo):
        """
        Add an error to group object.

        :param error: an error to add
        :return: None
        """
        logger.debug("Error in event {}, error_code: {}, detail {}".format(self.id, error.getErrorCode(),
                                                                           error.getErrorDescription()))
        self.error = {"error_code": error.getErrorCode(), "detail": error.getErrorDescription()}

    def addDescriptor(self, newDescriptorId):
        """
        Add a descriptor to a group.

        :param newDescriptorId:
        :return: None
        """
        self.descriptors.append(newDescriptorId)
        self.last_update = time()

    def __add__(self, other):
        """
        Merge an other group with the current into new one.

        :param other: other group to merge
        :return: new group
        """
        group = Group(self.group_policy)
        group.handler_id = self.handler_id
        group.source = self.source
        group.external_tracks_id = list(set(self.external_tracks_id + other.external_tracks_id))
        group.descriptors = list(set(other.descriptors + self.descriptors))
        group.ttl = max(self.ttl, other.ttl)
        group.create_time = min(self.create_time, other.create_time)
        group.events = list(set(other.events + self.events))
        group.tags = list(set(other.tags + self.tags))
        self.processed = True
        other.processed = True
        return group

    @property
    def dict(self):
        """
        Returns self.__dict__

        :return: self.__dict__
        """
        return self.__dict__

    @property
    def dictForJson(self) -> dict:
        """
        Create a dict from the group.

        :rtype: dict
        :return: json
        """
        groupDict = self.__dict__.copy()
        del groupDict["events"]
        del groupDict["group_policy"]
        return groupDict

    @property
    def json(self):
        """
        Returns the current group as json object.

        :return: json as string
        """
        return json.dumps(self.dictForJson, ensure_ascii = False)


class GroupsStorage:
    """
    Class to work with all groups.

    Attributes:
        currentGroups (Group[]): current (not processed) group list
    """
    def __init__(self):
        self.currentGroups = []

    def __getitem__(self, groupId):
        """
        Get group by id.

        :param groupId: id to get group by
        :return: return a group if group exist else return None
        """
        for group in self.currentGroups:
            if group.id == groupId:
                return group
        return None

    def getGroupByExternalIdAndHandlerId(self, externalId, handlerId, source = None):
        """
        Get group by the external_id and the handler_id.

        :param externalId: external id
        :param handlerId: handler id
        :param source: source of event
        :return: return a group if group exist else return None
        """
        for group in self.currentGroups:
            if externalId in group.external_tracks_id and group.source == source and group.handler_id == handlerId:
                return group
        return None

    def addDescriptorToGroup(self, groupId, descriptorId):
        """
        Add descriptor to a group

        :param groupId: group id
        :param descriptorId: descriptor id
        """
        for group in self.currentGroups:
            if groupId == group.id:
                group.addDescriptor(descriptorId)
                return True
        return False

    @lockGuard
    @gen.coroutine
    def getGroupsForHandlerAndSource(self, handler, source = None):
        """
        Close old groups and get group list for the handler with the corresponding source.
        With the guard.

        :param handler: handler id
        :param source: source
        :return: groups list
        """
        yield self.closeOldGroups_()

        if source is not None:
            groups = list(
                filter(lambda x: x.handler_id == handler and x.source == source and time() - x.last_update < x.ttl,
                       self.currentGroups))
        else:
            groups = list(filter(lambda x: x.handler_id == handler and time() - x.last_update < x.ttl,
                                 self.currentGroups))
        return groups

    def addNewGroup(self, descriptorId, handlerId, groupingPolicy, source = None, externalId = None):
        """
        Ad new group to the storage.

        :param descriptorId: descriptor id
        :param handlerId: handler id
        :param groupingPolicy: group policy
        :param source: source for group
        :param externalId: external id for group
        :return: group id
        """
        group = Group(groupingPolicy, source, externalId)
        group.addDescriptor(descriptorId)
        group.handler_id = handlerId
        self.currentGroups.append(group)
        return group.id

    @gen.coroutine
    def closeOldGroups_(self):
        """
        The group closes if the time period until the last event was added is greater than the group ttl.

        :return: None
        """
        currentTime = time()
        oldGroups = [s for s in self.currentGroups if currentTime - s.last_update >= s.ttl]
        for group in oldGroups:
            yield GROUP_CLOSE_QUEUE.putTask(group)
            logger.debug("Close group {}".format(group.id))
        self.currentGroups = [s for s in self.currentGroups if currentTime - s.last_update < s.ttl]

    @lockGuard
    @gen.coroutine
    def closeOldGroups(self):
        """
        Close groups with the guard.

        :return: None
        """
        yield self.closeOldGroups_()

    def addEventToGroupStorageInExternalIdCase(self, event, groupingPolicy):
        """
        Find group in the storage by external id. If Group was not found a new group will be created.
        Event is added to the group also.

        :param event: event
        :param groupingPolicy: group policy
        :return: group with event
        """
        group = self.getGroupByExternalIdAndHandlerId(event.external_id, event.handler_id, event.source)
        if group is None:
            event.group_id = self.addNewGroup(event.descriptor_id, event.handler_id, groupingPolicy,
                                              source = event.source,
                                              externalId = event.external_id)
            group = self.getGroupByExternalIdAndHandlerId(event.external_id, event.handler_id, event.source)
        else:
            event.group_id = group.id
            group.addDescriptor(event.descriptor_id)
        return group

    def addEventToGroupStorageInSimilarityCase(self, event, groupingPolicy) -> Group:
        """
        Find group in the storage by the event similarity. New group will be created if a group was not found.
        The event is added to the group also.

        :param event: event
        :param groupingPolicy: group policy
        :return: group with event
        """
        group = self[event.group_id]
        if group is None:
            event.group_id = self.addNewGroup(event.descriptor_id, event.handler_id, groupingPolicy,
                                              source = event.source)
            group = self[event.group_id]
        return group

    def addEventToGroupStorageInMixedCase(self, event, groupingPolicy):
        """
        Find group in the storage by external id and the event similarity.
        Another group will be created if a group was not found.

        :param event: event
        :param groupingPolicy: group policy
        :return: group with event
        :param event:
        :param groupingPolicy:
        :return: (<new group>, <list of groups to remove>) tuple
        """
        groupsForRemoving = None
        if event.external_id is not None:
            groupExternal = self.getGroupByExternalIdAndHandlerId(event.external_id, event.handler_id, event.source)
            groupSimilarity = self[event.group_id]
            if groupExternal is None and groupSimilarity is None:
                event.group_id = self.addNewGroup(event.descriptor_id, event.handler_id, groupingPolicy,
                                                  source = event.source, externalId = event.external_id)
                group = self[event.group_id]
            elif groupExternal is None and groupSimilarity is not None:
                event.group_id = groupSimilarity.id
                group = groupSimilarity
            elif groupExternal is not None and groupSimilarity is None:
                groupExternal.external_tracks_id.append(event.external_id)
                group = groupExternal
            else:
                if groupSimilarity == groupExternal:
                    group = groupExternal
                else:
                    self.currentGroups = [s for s in self.currentGroups if
                                          s.id not in [groupExternal.id, groupSimilarity.id]]
                    group = groupExternal + groupSimilarity
                    groupsForRemoving = [groupExternal, groupSimilarity]
                    group.addDescriptor(event.id)
                    self.currentGroups.append(group)
                    event.group_id = group.id
        else:
            group = self[event.group_id]
            if group is None:
                event.group_id = self.addNewGroup(event.descriptor_id, event.handler_id, groupingPolicy,
                                                  source = event.source, externalId = event.external_id)
                group = self[event.group_id]
        return group, groupsForRemoving

    @timer.timerTor
    @gen.coroutine
    def addNewEvent(self, event, groupingPolicy):
        """
        Add new event to the storage according to the group policy.

        :param event: event
        :param groupingPolicy: group policy
        :return: Result
        """
        groupsForRemoving = None

        if groupingPolicy.grouper == Grouper.EXTERNAL_ID:
            self.closeOldGroups_()
            if event.external_id is not None:
                group = self.addEventToGroupStorageInExternalIdCase(event, groupingPolicy)
            else:
                return Result(Error.Success, "without group")
        elif groupingPolicy.grouper == Grouper.SIMILARITY:
            group = self.addEventToGroupStorageInSimilarityCase(event, groupingPolicy)
        else:
            group, groupsForRemoving = self.addEventToGroupStorageInMixedCase(event, groupingPolicy)

        if group is None:
            return Result(Error.UnknownError, "group not found")
        updateRes = updateGroupFields(group, event, groupingPolicy)
        if updateRes.fail:
            return updateRes

        yield GROUP_UPDATE_QUEUE.putTask(group)
        if groupsForRemoving is not None:
            yield GROUP_UPDATE_GROUP_ID.putTask({"newGroup": group,
                                                 "oldGroups": groupsForRemoving})
        return Result(Error.Success, 0)


GROUPS_STORAGE = GroupsStorage()        #: global object for storing groups


@gen.coroutine
def periodicCleanGroups():
    """
    Run periodic groups closing.

    :return: None
    """
    yield GROUPS_STORAGE.closeOldGroups()
