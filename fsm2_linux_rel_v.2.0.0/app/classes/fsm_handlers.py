import copy
import functools
import ujson as json
import uuid
from datetime import datetime
from functools import wraps

from tornado import gen

from app.common_objects import ES_CLIENT as es
from app.common_objects import LUNA_CLIENT
from app.common_objects import logger
from app.common_objects import timer
from app.classes.descriptor_policy import DescriptorPolicy
from app.classes.events import Event, InputEvent
from app.classes.extract_policy import ExtractPolicy
from app.classes.grouping_policy import GroupPolicy
from app.classes.groups import GROUPS_STORAGE
from app.classes.person_policy import PersonPolicy
from app.classes.search_policy import SearchPolicy
from app.enums import *
from common.switch import switch
from errors.error import Result, Error


def processingStepExeptionWrap(func):
    """
    Decorator for catching exceptions in an asynchronous request.

    :param func: decorated asynchronous function
    :return: if exception was caught, system calls error method with error HandlerStepError.
    """

    @wraps(func)
    @gen.coroutine
    def wrap(*func_args, **func_kwargs):
        try:
            res = yield func(*func_args, **func_kwargs)
            return res
        except Exception:
            logger.exception()
            error = Error.generateError(Error.HandlerStepError,
                                        Error.HandlerStepError.getErrorDescription().format(func.__qualname__))
            return Result(error, 500)

    return wrap


class HandlerManager:
    """
    Class for getting handler from es.

    We cache results.
    """

    @classmethod
    @functools.lru_cache(maxsize = 100)
    @gen.coroutine
    def getHandler(cls, handlerId):
        """
        Get handler from ES by id with cache. Handlers should not change.

        :param handlerId: handler id.
        :return: in case of success Result(Error.Success, Matcherhandler(*)) or
                 Result(Error.Success, ExtractorHandler(*)) will be returned.
        """
        handlerDictRes = yield es.getHandler(handlerId)
        if handlerDictRes.fail:
            return handlerDictRes
        handlerDict = handlerDictRes.value
        handlerType = handlerDict["type"]
        if handlerType == "search":
            return Result(Error.Success, Matcherhandler(**handlerDict))
        else:
            return Result(Error.Success, ExtractorHandler(**handlerDict))

    @classmethod
    def clearCache(cls):
        """
        Remove cached handlers.

        :return: None
        """
        HandlerManager.getHandler.cache_clear()


def removeFieldFromDict(inputJson, target):
    """
    Recursive dict json field removal from json.

    :param inputJson: json
    :param target: filed for removing
    :return: json without fields
    """
    if type(inputJson) is dict:
        inputJson = {key: value for key, value in inputJson.items() if key != target}
        for element in inputJson:
            inputJson[element] = removeFieldFromDict(inputJson[element], target)
    if type(inputJson) is list:
        for number, element in enumerate(inputJson):
            inputJson[number] = removeFieldFromDict(element, target)
    return inputJson


class BaseHandler:
    """
    Base class for handler.
        This policy regulates how input image will be extracted, searched, linked with person and attached to
        a Luna API list.

    Attributes:
        id (UUID4): the handler id
        name (str): a handler user description.
        descriptor_policy (DescriptorPolicy):  this policy regulates attach descriptors to luna lists.
        multiple_faces_policy(int): to process several faces in one image or not, available only for "extract" handlers,
                                    if grouping_policy is not None this step will be skipped.
        extract_policy (ExtractPolicy): this policy regulates how input image will be extracted.
        grouping_policy (GroupPolicy): this policy regulates the attaching events to group process.
        person_policy (PersonPolicy): this policy regulates the attaching descriptor to person process.
    """
    def __init__(self, **kwargs):

        self.search_policy = None
        self.multiple_faces_policy = None
        self.id = None
        if "name" in kwargs:
            self.name = kwargs["name"]
        else:
            self.name = "Handler {}".format(datetime.now())

        if "id" in kwargs:
            self.id = kwargs["id"]
        else:
            self.id = str(uuid.uuid4())

        self.descriptor_policy = None
        if "descriptor_policy" in kwargs:
            if kwargs["descriptor_policy"] is not None:
                self.descriptor_policy = DescriptorPolicy(**kwargs["descriptor_policy"])

        self.extract_policy = ExtractPolicy()
        if "extract_policy" in kwargs:
            if kwargs["extract_policy"] is not None:
                self.extract_policy = ExtractPolicy(**kwargs["extract_policy"])

        self.grouping_policy = None
        if "grouping_policy" in kwargs:
            if kwargs["grouping_policy"] is not None:
                self.grouping_policy = GroupPolicy(**kwargs["grouping_policy"])

        self.person_policy = None
        if "person_policy" in kwargs:
            if kwargs["person_policy"] is not None:
                self.person_policy = PersonPolicy(True, **kwargs["person_policy"])

    @property
    def dict(self):
        """
        Create dict from class.

        :return: dict.
        """
        return self.__dict__

    @property
    def json(self) -> str:
        """
        Creating json from handler

        :rtype: str
        :return: json
        """
        js = copy.deepcopy(json.loads(json.dumps(self.dict, ensure_ascii = False)))
        js = removeFieldFromDict(js, "type")
        js["type"] = self.dict["type"]
        return json.dumps(js, ensure_ascii = False)

    @gen.coroutine
    def finishStep(self, event: Event) -> Result:
        """
        Execute the descriptor_policy and the person_policy.

        :param event: event
        :return: Result(Error.Success, 0)
        """
        futuresOfSteps = []
        if self.descriptor_policy is not None:
            futuresOfSteps.append(self.descriptor_policy.executePolicy(event))
        if self.person_policy is not None:
            futuresOfSteps.append(self.person_policy.executePolicy(event))
        yield futuresOfSteps
        return Result(Error.Success, 0)

    def getProcessingEventSteps(self):
        raise NotImplementedError

    @timer.timerTor
    @processingStepExeptionWrap
    @gen.coroutine
    def groupStep(self, event: Event):
        """
        Run the grouping step coroutine.

        :param event: an event to search in group
        :return: a group search result
        """
        groupSearchRes = yield self.searchGroup(event)
        return groupSearchRes

    @timer.timerTor
    @processingStepExeptionWrap
    @gen.coroutine
    def searchGroup(self, event):
        """
        Search event in open groups.

        :param event: event to search
        :return: result
            Success if succeed
            Fail if an error occurred
        """

        currentGroups = yield GROUPS_STORAGE.getGroupsForHandlerAndSource(self.id, event.source)
        descriptors = []
        for group in currentGroups:
            descriptors = list(set(descriptors + group.descriptors))

        if len(descriptors) == 0:
            return Result(Error.Success, None)

        searchReply = yield LUNA_CLIENT.search(body = event.img, limit = 1,
                                               warpedImage = event.warped_img,
                                               **self.extract_policy.dict(), descriptorIds = descriptors)
        if searchReply.success:
            event.id = searchReply.body["face"]["id"]
            event.extract = searchReply.body["face"]
            event.descriptor_id = searchReply.body["face"]["id"]
            event.search_by_group = {"candidates": searchReply.body["candidates"]}
            logger.debug("SIMILARITY: {}".format(event.search_by_group["candidates"][0]["similarity"]))
            if event.search_by_group["candidates"][0]["similarity"] < self.grouping_policy.threshold:
                for case in switch(self.grouping_policy.grouper):
                    if case(Grouper.SIMILARITY):
                        event.group_id = GROUPS_STORAGE.addNewGroup(event.descriptor_id, self.id,
                                                                    self.grouping_policy,
                                                                    source = event.source)
                        return Result(Error.Success, None)

                    if case(Grouper.MIXED):
                        if event.external_id is not None:
                            groupId = GROUPS_STORAGE.getGroupByExternalIdAndHandlerId(event.external_id, event.handler_id,
                                                                                      event.source)

                            if groupId is not None:
                                resUpdate = GROUPS_STORAGE.addDescriptorToGroup(groupId.id, event.id)
                                if resUpdate:
                                    event.group_id = groupId.id
                                    return Result(Error.Success, None)

                        event.group_id = GROUPS_STORAGE.addNewGroup(event.descriptor_id, self.id,
                                                                    self.grouping_policy,
                                                                    source = event.source,
                                                                    externalId = event.external_id)
                        return Result(Error.Success, None)

                    if case():
                        return Result(Error.UnknownError, "Wrong group policy: {}".format(self.grouping_policy.grouper))

            mostSimilarityDescriptor = event.search_by_group["candidates"][0]["id"]
            for group in currentGroups:
                if mostSimilarityDescriptor in group.descriptors:
                    event.group_id = group.id
                    logger.debug(
                        "UPDATE GROUP : {}, {} {} ".format(group.id, event.descriptor_id, mostSimilarityDescriptor))
                    successUpdate = GROUPS_STORAGE.addDescriptorToGroup(group.id, event.descriptor_id)
                    if successUpdate:
                        return Result(Error.Success, event.group_id)
                    else:
                        event.group_id = GROUPS_STORAGE.addNewGroup(event.descriptor_id, self.id,
                                                                    self.grouping_policy, source = event.source)
                        return Result(Error.Success, None)

            logger.error("No group was found while executing the group policy")
            return Result(Error.InternalServerError, "No group was found while executing the group policy")
        else:
            event.id = str(uuid.uuid4())
            event.error = searchReply.body
            logger.error(searchReply.body)
            error = Error.generateLunaError("Search by group", searchReply.body)
            event.setError(error)
            return Result(error, searchReply.statusCode)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)


class Matcherhandler(BaseHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "search"
        self.search_policy = SearchPolicy(**kwargs["search_policy"])

    @timer.timerTor
    @gen.coroutine
    def searchByList(self, searchList, eventForSearching):
        """
        Search by Luna API list policy implementation.

        :param searchList: Luna API list to search by, represented as a dictionary with "list_id", "list_type", "limit"
            keys with corresponding values
        :param eventForSearching: event to search
        :return: result
            Success with candidates if succeed
            Fail if an error occurred
        """
        listId = searchList["list_id"]
        listType = searchList["list_type"]
        limit = searchList["limit"]
        if eventForSearching.needExtract:
            searchReply = yield LUNA_CLIENT.search(body = eventForSearching.img, limit = limit,
                                                   warpedImage = eventForSearching.warped_img,
                                                   **self.extract_policy.dict(), listId = listId)
            if searchReply.success:
                eventForSearching.id = searchReply.body["face"]["id"]
                eventForSearching.extract = searchReply.body["face"]
                eventForSearching.descriptor_id = searchReply.body["face"]["id"]
            elif searchReply.statusCode == 400:
                if searchReply.body["error_code"] == 11012:
                    return Result(Error.MultipleFacesError, searchReply.body["detail"]["faces"])
        else:
            if listType == "persons":
                searchReply = yield LUNA_CLIENT.identify(descriptorId = eventForSearching.id, listId = listId,
                                                         limit = limit)
            else:
                searchReply = yield LUNA_CLIENT.match(descriptorId = eventForSearching.id, listId = listId,
                                                      limit = limit)
        if searchReply.success:
            return Result(Error.Success, searchReply.body["candidates"])
        else:
            logger.error(searchReply.body)
            error = Error.generateLunaError("'Match'", searchReply.body)
            eventForSearching.setError(error)
            return Result(error, searchReply.statusCode)

    @staticmethod
    def stopSearch(searchPriority, searchListResult, listThreshold):
        """
        If we need to stop search.

        :param searchPriority: The search by lists priority.
            * 1 - Search is done on all lists, the results are combined.
            * 2 - the search is in order, if the result of the match on some list has exceeded *threshold*, the search stops.
        :param searchListResult:
        :param listThreshold:
        :return: True or False
        """
        return len(searchListResult) and listThreshold <= searchListResult[0]["similarity"] and searchPriority == 2

    @timer.timerTor
    @gen.coroutine
    def searchStep(self, event: Event) -> Result:
        """
        Search part of the handler. Main function for search-type handlers.

        :param event: event to search
        :return: result
            Success with event if succeed
            Fail if an error occurred
        """
        priority = self.search_policy.search_priority
        searchResult = []

        generateSearchResult = lambda x, y: {"list_id": x["list_id"], "candidates": y}

        if event.needExtract:
            searchByListRes = yield self.searchByList(self.search_policy.search_lists[0], event)
            if searchByListRes.fail:
                return searchByListRes

            searchResult.append(generateSearchResult(self.search_policy.search_lists[0], searchByListRes.value))

            if Matcherhandler.stopSearch(priority, searchByListRes.value,
                                         self.search_policy.search_lists[0]["threshold"]):
                event.search = searchResult
                return Result(Error.Success, event)
            listsForSearch = self.search_policy.search_lists[1:]
        else:
            listsForSearch = self.search_policy.search_lists

        searchFutures = []
        for listForSearch in listsForSearch:
            searchFutures.append((self.searchByList(listForSearch, event), listForSearch))

        for future in searchFutures:
            searchByListRes = yield future[0]
            if searchByListRes.fail:
                return searchByListRes

            searchResult.append(generateSearchResult(future[1], searchByListRes.value))
            if Matcherhandler.stopSearch(priority, searchByListRes.value,
                                         self.search_policy.search_lists[0]["threshold"]):
                event.search = searchResult
                return Result(Error.Success, event)

        event.search = searchResult
        return Result(Error.Success, event)

    def getProcessingEventSteps(self):
        """
        Get the event processing steps according to existing policies in the router.

        :return: list of steps
        """
        steps = []
        if self.grouping_policy is not None:
            if self.grouping_policy.grouper in [Grouper.MIXED, Grouper.SIMILARITY]:
                steps.append(self.groupStep)
        steps.append(self.searchStep)
        if self.person_policy is not None or self.descriptor_policy is not None:
            steps.append(self.finishStep)
        return steps

    @timer.timerTor
    @gen.coroutine
    def process(self, inputEvent: InputEvent):
        """
        Process an input event through processing steps.

        :param inputEvent:
        :return: result
            Success with event if succeed
            Fail if an error occurred
        """
        event = inputEvent.generateEvent()
        processingSteps = self.getProcessingEventSteps()
        for processingStep in processingSteps:
            result = yield processingStep(event)
            if result.fail:
                return result

        if self.grouping_policy is not None:
            logger.debug("update groups {}".format(self.id))
            yield GROUPS_STORAGE.addNewEvent(event, self.grouping_policy)
        return Result(Error.Success, event)


class ExtractorHandler(BaseHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "extract"
        self.multiple_faces_policy = kwargs["multiple_faces_policy"]

    @timer.timerTor
    @processingStepExeptionWrap
    @gen.coroutine
    def extractStep(self, event: Event) -> Result:
        """
        Extract step of the handler. Main function for extract-type handlers.

        :param event: event to extract
        :return: result
            Success with extract status code if succeed
            Fail if an error occurred
        """
        extractReply = yield LUNA_CLIENT.extractDescriptors(body = event.img,
                                                            warpedImage = event.warped_img,
                                                            **self.extract_policy.dict())

        if extractReply.success:
            if len(extractReply.body["faces"]) > 1:
                if self.multiple_faces_policy and self.grouping_policy is None:
                    events = []
                    for face in extractReply.body["faces"]:
                        ev = copy.deepcopy(event)
                        ev.id = face["id"]
                        ev.extract = face
                        ev.descriptor_id = face["id"]
                        ev.img = event.img
                        events.append(ev)
                    return Result(Error.Success, events)
                else:
                    event.setError(Error.MultipleFacesError)
                    event.extract = extractReply.body["faces"]
                    return Result(Error.MultipleFacesError, extractReply.body["faces"])
            else:
                face = extractReply.body["faces"][0]
                event.id = face["id"]
                event.extract = face
                event.descriptor_id = face["id"]
                return Result(Error.Success, [event])

        else:
            logger.error(extractReply.body)
            error = Error.generateLunaError("'Extract'", extractReply.body)
            event.setError(error)
            return Result(error, extractReply.statusCode)

    def getProcessingEventSteps(self):
        """
        Get the event processing steps according to existing policies in the router.

        :return: list of steps
        """
        steps = []
        if self.person_policy is not None or self.descriptor_policy is not None:
            steps.append(self.finishStep)
        return steps

    @timer.timerTor
    @gen.coroutine
    def process(self, inputEvent: InputEvent):
        """
        Process an input event through processing steps.

        :param inputEvent: input event
        :return: result
            Success with events if succeed
            Fail if an error occurred
        """
        event = inputEvent.generateEvent()
        events = [event]
        if self.grouping_policy is not None:
            if self.grouping_policy.grouper in [Grouper.MIXED, Grouper.SIMILARITY]:
                groupRes = yield self.groupStep(events[0])
                if groupRes.fail:
                    return groupRes

        if events[0].id is None:
            extractRes = yield self.extractStep(events[0])
            if extractRes.fail:
                return extractRes
            events = extractRes.value

        if self.person_policy is not None or self.descriptor_policy is not None:
            @gen.coroutine
            def finishProcessingEvent(finishingEvent):
                yield self.finishStep(finishingEvent)

            yield [finishProcessingEvent(event) for event in events]

        if self.grouping_policy is not None:
            yield GROUPS_STORAGE.addNewEvent(events[0], self.grouping_policy)

        return Result(Error.Success, events)
