from tests.system_tests.base_test_class import BaseTest
import time
from tests.system_tests.fsmRequests import *
from tests.system_tests.shemas import *
from jsonschema import validate

personsImgs = [["./data/girl_1_0.jpg"],
               ["./data/girl_1_1.jpg"],
               ["./data/girl_1_2.jpg"]]

descriptorsImg = [["./data/girl_2_0.jpg"],
                  ["./data/girl_2_1.jpg"],
                  ["./data/girl_2_2.jpg"]]


def createTestSearchHandler(name, searchLists, priority=1, descriptorPolicy=None, extractPolicy=None,
                            groupingPolicy=None, personPolicy=None):
    handler = {
        "name": "test_visionlabs_handlers_{}".format(name),
        "type": "search",
        "search_policy": {
            "search_lists": searchLists,
            "search_priority": priority
        }
    }
    if descriptorPolicy is not None:
        handler["descriptor_policy"] = descriptorPolicy
    if extractPolicy is not None:
        handler["extract_policy"] = extractPolicy
    else:
        handler["extract_policy"] = {
            "estimate_attributes": 1
        }
    if groupingPolicy is not None:
        handler["grouping_policy"] = groupingPolicy
    if personPolicy is not None:
        handler["person_policy"] = personPolicy
    return handler


def createTestHandler(handlerType, **handlerKwargs):
    if handlerType == "search":
        handler = createTestSearchHandler(searchLists=BaseTestsHandlersPolicies.createStandardSearchPolicy(),
                                          **handlerKwargs)
    else:
        handler = createTestextractHandler(**handlerKwargs)
    reply = createHandler(handler)
    handler["id"] = reply.json["handler_id"]
    return handler


def createTestextractHandler(name, multipleFacesPolicy=0, descriptorPolicy=None, extractPolicy=None,
                             groupingPolicy=None, personPolicy=None):
    handler = {
        "name": "test_visionlabs_extract_handler_{}".format(name),
        "type": "extract",
        "multiple_faces_policy": multipleFacesPolicy
    }
    if descriptorPolicy is not None:
        handler["descriptor_policy"] = descriptorPolicy

    if extractPolicy is not None:
        handler["extract_policy"] = extractPolicy
    else:
        handler["extract_policy"] = {
            "estimate_attributes": 1
        }
    if groupingPolicy is not None:
        handler["grouping_policy"] = groupingPolicy
    if personPolicy is not None:
        handler["person_policy"] = personPolicy
    return handler


def createSimpleDescriptorPolicy(listId, filters):
    policy = {
        "attach_policy": {
            "filters": filters,
            "list_id": listId
        }
    }
    return policy


from functools import wraps


def singelton(func):
    instances = {}

    @wraps(func)
    def wrap(self, *func_args, **func_kwargs):
        if not func.__qualname__ in instances:
            res = func(self, *func_args, **func_kwargs)
            instances[func.__qualname__] = res
            return res
        return instances[func.__qualname__]

    return wrap


class BaseTestsHandlersPolicies(BaseTest):
    name = 'test_visionlabs_base_tests_handlers_policies'
    personsMatchingLists = []
    descriptorsMatchingLists = []
    personsAttachLists = []
    descriptorsAttachLists = []
    creatingPersons = []
    tempList = []
    warped_flags = [1, -1, 0]

    @staticmethod
    def createBlockListForTests(listType, listData, count, storage):
        for i in range(count):
            res = BaseTestsHandlersPolicies.lunaClient.createList(listType, listData.format(i), True)
            storage.append(res.body["list_id"])

    @staticmethod
    def fillPersonsMatchingList(lists):
        for count, lunaList in enumerate(lists):
            for filename in personsImgs[count]:
                reply = BaseTestsHandlersPolicies.lunaClient.createPerson(BaseTestsHandlersPolicies.name,
                                                                          raiseError=True)
                personId = reply.body["person_id"]
                BaseTestsHandlersPolicies.creatingPersons.append(personId)
                BaseTestsHandlersPolicies.lunaClient.linkListToPerson(personId, lunaList, raiseError=True)
                reply = BaseTestsHandlersPolicies.lunaClient.extractDescriptors(filename=filename, raiseError=True,
                                                                                warpedImage=True)
                descriptorId = reply.body["faces"][0]["id"]
                BaseTestsHandlersPolicies.lunaClient.linkDescriptorToPerson(personId, descriptorId, raiseError=True)

    @staticmethod
    def fillDescriptorsMatchingList(lists):
        for count, lunaList in enumerate(lists):
            for filename in descriptorsImg[count]:
                reply = BaseTestsHandlersPolicies.lunaClient.extractDescriptors(filename=filename, raiseError=True,
                                                                                warpedImage=True)
                descriptorId = reply.body["faces"][0]["id"]
                BaseTestsHandlersPolicies.lunaClient.linkListToDescriptor(descriptorId, lunaList, raiseError=True)

    def checkEventFSM(self, event, handlerName):
        eventId = event["id"]
        reply = getEvent(eventId)
        self.assertEqual(event, reply.json, handlerName)

    def checkEvent(self, event, handler, descriptorLists=None, checkPerson=False, personsList=None):
        self.checkEventFSM(event, handler["name"])
        self.assertTrue(event["error"] is None, handler["name"])
        if descriptorLists is not None:
            self.assertEqual(set(descriptorLists),
                             set(event["descriptors_lists"]), handler["name"])
            descriptorListsInLuna = BaseTestsHandlersPolicies.lunaClient.getLinkedListsToDescriptor(event["id"])
            self.assertEqual(set(descriptorLists), set(descriptorListsInLuna.body["lists"]), handler["name"])
        if checkPerson or personsList is not None:
            self.assertTrue(event["person_id"] is not None, handler["name"])
            personId = event["person_id"]
            person = BaseTestsHandlersPolicies.lunaClient.getPerson(personId)
            self.assertEqual(person.body["descriptors"], [event["id"]], handler["name"])
        if personsList is not None:
            personId = event["person_id"]
            personListsInLuna = BaseTestsHandlersPolicies.lunaClient.getLinkedListsToPerson(personId)
            self.assertEqual(set(personsList), set(personListsInLuna.body["lists"]), handler["name"])

    def checkGroup(self, group, handler, descriptors, checkPerson=False, personsLists=None, withoutError=True):

        if withoutError:
            self.assertTrue(group["error"] is None, handler["name"])

        self.assertEqual(set(descriptors), set(group["descriptors"]), handler["name"])
        if checkPerson or personsLists is not None:
            self.assertTrue(group["person_id"] is not None, handler["name"])
            personId = group["person_id"]
            person = BaseTestsHandlersPolicies.lunaClient.getPerson(personId)
            self.assertEqual(set(person.body["descriptors"]), set(group["descriptors"]), handler["name"])
        if personsLists is not None:
            personId = group["person_id"]
            personListsInLuna = BaseTestsHandlersPolicies.lunaClient.getLinkedListsToPerson(personId)
            self.assertEqual(set(personsLists), set(personListsInLuna.body["lists"]), handler["name"])

    def validateEvent(self, reply, handler, descriptorsLists=None, checkPerson=False, personsLists=None):
        self.assertEqual(reply.statusCode, 201, handler["name"])
        if handler["type"] == "search":
            self.assertTrue(validate(reply.json, SEARCH_EVENT_SCHEMA) is None, handler["name"])
        else:
            self.assertTrue(validate(reply.json, EXTRACT_EVENT_SCHEMA) is None, handler["name"])

        self.checkEvent(reply.json["events"][0], handler, descriptorsLists, checkPerson, personsLists)

    def validateGroup(self, reply, handler, descriptors, personsLists=None, checkPerson=False, withoutError=True):
        self.assertTrue(validate(reply.json, GROUP_SCHEMA) is None, handler["name"])
        self.checkGroup(reply.json, handler, descriptors, checkPerson, personsLists, withoutError)

    def validateGroups(self, testingGroups, handler):
        for testingGroup in testingGroups:
            reply = getGroup(testingGroup.groupId)
            self.validateGroup(reply, handler, testingGroup.events, testingGroup.personsLists,
                               testingGroup.createPerson)

    def uploadGroups(self, testingGroups, countEventsForGroup):
        for countEvent in range(countEventsForGroup):
            for testingGroup in testingGroups:
                testingGroup.emitEvent()

    @staticmethod
    def emitNeutralImg(neutralImg, handlerId):
        emitEvent(handlerId, neutralImg, queryParams={"warped_image": 1})

    @staticmethod
    def closeGroupsOfhandler(neutralImg, handlerId):
        time.sleep(10)
        BaseTestsHandlersPolicies.emitNeutralImg(neutralImg, handlerId)
        time.sleep(2)

    @staticmethod
    def createStandardSearchPolicy():
        return [
            {"list_id": BaseTestsHandlersPolicies.personsMatchingLists[i], "threshold": 0.11, "list_type": "persons",
             "limit": 1
             } for i in range(3)]

    @classmethod
    @singelton
    def setUpClass(cls):

        BaseTestsHandlersPolicies.createBlockListForTests("persons", "test_fsm_visionlabs_matching_persons_list_{}", 3,
                                                          BaseTestsHandlersPolicies.personsMatchingLists)
        BaseTestsHandlersPolicies.createBlockListForTests("persons", "test_fsm_visionlabs_attaching_persons_list_{}", 3,
                                                          BaseTestsHandlersPolicies.personsAttachLists)
        BaseTestsHandlersPolicies.createBlockListForTests("descriptors",
                                                          "test_fsm_visionlabs_matching_descriptors_list_{}", 3,
                                                          BaseTestsHandlersPolicies.descriptorsMatchingLists)
        BaseTestsHandlersPolicies.createBlockListForTests("descriptors",
                                                          "test_fsm_visionlabs_attaching_descriptors_list_{}", 3,
                                                          BaseTestsHandlersPolicies.descriptorsAttachLists)

        BaseTestsHandlersPolicies.fillPersonsMatchingList(BaseTestsHandlersPolicies.personsMatchingLists)
        BaseTestsHandlersPolicies.fillDescriptorsMatchingList(BaseTestsHandlersPolicies.descriptorsMatchingLists)

    @staticmethod
    def createBigList(imgs):
        listId = BaseTestsHandlersPolicies.lunaClient.createList("descriptors",
                                                                 "test_fsm_visionlabs_matching_descriptors_big_list",
                                                                 raiseError=True).body["list_id"]
        descriptors = []
        for img in imgs:
            descriptorId = BaseTestsHandlersPolicies.lunaClient.extractDescriptors(filename=img, warpedImage=True,
                                                                                   raiseError=True).body["faces"][0][
                "id"]
            BaseTestsHandlersPolicies.lunaClient.linkListToDescriptor(descriptorId, listId, raiseError=True)
            descriptors.append(descriptorId)
        BaseTestsHandlersPolicies.tempList.append(listId)
        return listId, descriptors

    @classmethod
    def tearDownClass(cls):
        super(BaseTestsHandlersPolicies, cls).tearDownClass()
        cls.deleteLunaAPIPersons(BaseTestsHandlersPolicies.creatingPersons)
        cls.deleteLunaAPILists(
            BaseTestsHandlersPolicies.personsMatchingLists + BaseTestsHandlersPolicies.descriptorsMatchingLists +
            BaseTestsHandlersPolicies.personsAttachLists + BaseTestsHandlersPolicies.descriptorsAttachLists +
            BaseTestsHandlersPolicies.tempList)
