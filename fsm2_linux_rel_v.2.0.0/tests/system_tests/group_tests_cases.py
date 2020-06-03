import copy
import uuid
from tests.system_tests.base_test_handlers_logic import emitEvent, createHandler, createTestHandler, BaseTestsHandlersPolicies, createTestSearchHandler


def generateBaseGroupPolicy(grouper=1):
    groupingPolicy = {
        "ttl": 10,
        "grouper": grouper,
        "threshold": 0.3}
    return copy.deepcopy(groupingPolicy)


class TestGroup:
    def __init__(self, handler, imgsForGroup, externalId=None, source=None, personsLists=None,
                 createPerson=False, countImgForTestPrepare=3):
        self.groupId = None
        self.events = []
        self.externalId = externalId
        self.imgsForGroup = imgsForGroup
        self.countSentEvents = 0
        self.handler = handler
        self.groupSource = source
        self.personsLists = personsLists
        self.createPerson = createPerson
        self.countImgForTestPrepare = countImgForTestPrepare

    def generateQueryParams(self):
        queryParams = {"warped_image": 1}
        if self.externalId is not None:
            queryParams["external_id"] = self.externalId
        if self.groupSource is not None:
            queryParams["source"] = self.groupSource
        return queryParams

    def emitEvent(self):
        if self.countSentEvents == len(self.imgsForGroup):
            return

        queryParams = self.generateQueryParams()
        reply = emitEvent(self.handler["id"], self.imgsForGroup[self.countSentEvents], queryParams)
        if self.countSentEvents == 0:
            self.groupId = reply.json["events"][0]["group_id"]
        else:
            assert self.groupId == reply.json["events"][0]["group_id"], reply.json
        assert self.groupId is not None
        assert self.handler["id"] == reply.json["events"][0]["handler_id"]
        self.events.append(reply.json["events"][0]["id"])
        self.countSentEvents += 1


class GroupHandlerTestCase:
    def __init__(self, handler, groups, description):
        self.handler = handler
        self.groups = groups
        self.description = description


def group_generator_test_handlers_group_simple_policy(handlerType, grouper):
    groupPolicy = generateBaseGroupPolicy(grouper)
    handler = createTestHandler(handlerType, name="group_simple_policy{}".format(grouper),
                                groupingPolicy=groupPolicy)
    testGroups = []
    for t in range(2):
        if grouper == 1:
            testGroups.append(TestGroup(handler, ["./data/girl_{}_{}.jpg".format(1, j)
                                                  for j in range(3)], externalId=146 + t))
        else:
            testGroups.append(TestGroup(handler, ["./data/girl_{}_{}.jpg".format(t + 1, j)
                                                  for j in range(3)]))
    return GroupHandlerTestCase(handler, testGroups,
                                "test_handlers_group_simple_policy_{}_{}".format(handlerType, grouper))


def group_generator_test_handlers_group_mixed_policy(handlerType):
    groupPolicy = {"ttl": 20,
                   "grouper": 3,
                   "threshold": 0.5}

    handler = createTestHandler(handlerType, name="group_mixed_policy",
                                groupingPolicy=groupPolicy)

    testGroup1 = TestGroup(handler, ["./data/girl_old.jpg",
                                     "./data/girl_1_1.jpg",
                                     "./data/girl_young.jpg"], externalId=146, countImgForTestPrepare=2)
    testGroup2 = TestGroup(handler, ["./data/girl_2_2.jpg",
                                     "./data/girl_young.jpg",
                                     "./data/girl_1_0.jpg"], externalId=147, countImgForTestPrepare=2)
    testGroup3 = TestGroup(handler, ["./data/man_1_0.jpg",
                                     "./data/man_1_1.jpg",
                                     "./data/man_old.jpg"], externalId=148, countImgForTestPrepare=2)
    testGroups = [testGroup1, testGroup2, testGroup3]
    return GroupHandlerTestCase(handler, testGroups, "test_handlers_group_simple_policy_{}".format(handlerType))


def group_generator_test_handlers_group_search_aggregator(lunaList, searchType):
    groupPolicy = generateBaseGroupPolicy()
    groupPolicy["search"] = searchType
    handler = createTestSearchHandler("search_aggregator", searchLists=[
        {"list_id": lunaList, "threshold": 0.11, "list_type": "descriptors", "limit": 5
         }], groupingPolicy=groupPolicy)

    reply = createHandler(handler)
    handler["id"] = reply.json["handler_id"]

    testGroups = []
    for t in range(2):
        externalId = 146 + t
        testGroups.append(TestGroup(handler, ["./data/girl_{}_{}.jpg".format(t + 1, j)
                                              for j in range(3)], externalId=externalId, createPerson=True))
    testGroups[0].imgsForGroup[1], testGroups[1].imgsForGroup[1] = \
        testGroups[1].imgsForGroup[1], testGroups[0].imgsForGroup[1]
    case = GroupHandlerTestCase(handler, testGroups, "test_handlers_group_search_aggregator_{}".format(searchType))
    case.searchType = searchType
    case.searchList = lunaList
    return case


def createBigList():
    imgsForSearching = ["./data/girl_1_0.jpg",
                        "./data/girl_2_0.jpg",
                        "./data/man_1_1.jpg",
                        "./data/man_1_0.jpg",
                        "./data/man_old.jpg"]

    lunaList, descriptorsInList = BaseTestsHandlersPolicies.createBigList(imgsForSearching)
    return lunaList


def group_generator_test_handlers_group_gender_aggregator(handlerType, genderAggregatorType):
    groupPolicy = generateBaseGroupPolicy()
    groupPolicy["gender"] = genderAggregatorType

    handler = createTestHandler(handlerType, name="group_gender_aggregator_{}".format(handlerType),
                                groupingPolicy=groupPolicy)
    testGroups = [TestGroup(handler, ["./data/girl_{}_{}.jpg".format(t + 1, j) for j in range(3)],
                            externalId=146 + t, createPerson=True) for t in range(2)]
    case = GroupHandlerTestCase(handler, testGroups, "test_handlers_group_gender_aggregator_{}".format(handlerType))
    case.genderAggregatorType = genderAggregatorType
    return case


def group_generator_test_handlers_group_age_aggregator(handlerType):
    groupPolicy = generateBaseGroupPolicy()
    groupPolicy["age"] = 1

    handler = createTestHandler(handlerType, name="group_age_aggregator",
                                groupingPolicy=groupPolicy)

    testGroups = [TestGroup(handler, ["./data/girl_{}_{}.jpg".format(1, j)
                                      for j in range(3)], externalId=146, createPerson=True)]
    case = GroupHandlerTestCase(handler, testGroups, "test_handlers_group_age_aggregator_{}".format(handlerType))
    return case


def group_generator_test_handlers_group_simple_create_person(handlerType):
    groupPolicy = generateBaseGroupPolicy()
    groupPolicy["create_person_policy"] = {
        "create_person": 1
    }

    handler = createTestHandler(handlerType, name="group_simple_create_person",
                                groupingPolicy=groupPolicy)

    testGroups = [(TestGroup(handler, ["./data/girl_{}_{}.jpg".format(t + 1, j) for j in range(1)],
                             externalId=146 + t, countImgForTestPrepare=1, createPerson=True)) for t in range(2)]
    case = GroupHandlerTestCase(handler, testGroups, "test_handlers_group_simple_create_person_{}".format(handlerType))
    return case


def group_generator_test_handlers_group_create_person_with_one_filters(handlerType, filterType):
    groupPolicy1 = generateBaseGroupPolicy()
    groupPolicy1["age"] = 1
    groupPolicy1["create_person_policy"] = {
        "create_person": 1,
        "create_filters":
            {
                "gender": 1
            }
    }
    groupPolicy2 = generateBaseGroupPolicy()
    groupPolicy2["age"] = 1
    groupPolicy2["create_person_policy"] = {
        "create_person": 1,
        "create_filters":
            {
                "age_range": {"start": 30, "end": 60}
            }
    }
    groupPolicies = [groupPolicy1, groupPolicy2]
    if handlerType == "search":
        groupPolicy3 = generateBaseGroupPolicy()
        groupPolicy3["age"] = 1
        groupPolicy3["create_person_policy"] = {
            "create_person": 1,
            "create_filters":
                {
                    "similarity_filter":
                        {
                            "policy": 1,
                            "lists": [{
                                "list_id": matchingList,
                                "threshold": 0.99
                            } for matchingList in BaseTestsHandlersPolicies.personsMatchingLists]
                        }
                }
        }
        groupPolicies.append(groupPolicy3)

    groupPolicy = groupPolicies[filterType]

    handler = createTestHandler(handlerType,
                                name="create_person_from_group_with_filter_{}".format(filterType),
                                groupingPolicy=groupPolicy)

    data = [
        "./data/man_young.jpg",
        "./data/girl_old.jpg"
    ]
    if handlerType == "search":
        data.append("./data/girl_1_0.jpg")

    testGroups = [TestGroup(handler, [data[j]], externalId=146 + j,
                            createPerson=(j == filterType), countImgForTestPrepare=1) for j in range(len(data))]
    case = GroupHandlerTestCase(handler, testGroups,
                                "test_handlers_group_create_person_with_one_filters_{}_{}".format(handlerType,
                                                                                                  filterType))
    return case


def group_generator_test_handlers_group_create_person_with_several_filters(handlerType):
    groupPolicy = generateBaseGroupPolicy()
    groupPolicy["create_person_policy"] = {
        "create_person": 1,
        "create_filters":
            {
                "gender": 0,
                "age_range": {"start": 20, "end": 22},
            }
    }
    testGroups = []
    if handlerType == "search":
        groupPolicy["create_person_policy"]["create_filters"]["similarity_filter"] = {
            "policy": 1,
            "lists": [{
                "list_id": matchingList,
                "threshold": 0.99
            } for matchingList in BaseTestsHandlersPolicies.personsMatchingLists]}
        handler = createTestHandler(handlerType,
                                    name="group_create_person_with_several_filters",
                                    groupingPolicy=groupPolicy)
    else:

        handler = createTestHandler(handlerType,
                                    name="group_create_person_with_several_filters",
                                    groupingPolicy=groupPolicy)

    testGroups += [TestGroup(handler, ["./data/girl_{}_{}.jpg".format(1, j)], externalId=146 + j,
                             createPerson=(j == 0), countImgForTestPrepare=1) for j in range(2)]

    case = GroupHandlerTestCase(handler, testGroups,
                                "test_handlers_group_create_person_with_several_filters_{}".format(
                                    handlerType))
    return case


def group_generator_test_handlers_group_ttl(handlerType, grouperType):
    groupPolicy = generateBaseGroupPolicy(grouperType)

    handler = createTestHandler(handlerType, name="group_ttl_{}".format(grouperType),
                                groupingPolicy=groupPolicy)

    testGroups = []
    for t in range(2):
        externalId = None
        if grouperType == 1:
            externalId = 146 + t
            testGroups.append(TestGroup(handler, ["./data/girl_{}_{}.jpg".format(1, j) for j in range(1)],
                                        externalId=externalId, countImgForTestPrepare=1))
        else:
            testGroups.append(TestGroup(handler, ["./data/girl_{}_{}.jpg".format(t + 1, j) for j in range(1)],
                                        externalId=externalId, countImgForTestPrepare=1))
    case = GroupHandlerTestCase(handler, testGroups,
                                "test_handlers_group_ttl_{}_{}".format(handlerType, grouperType))
    return case


def group_generator_test_handlers_group_source(handlerType, grouperType):
    groupPolicy = generateBaseGroupPolicy(grouperType)

    handler = createTestHandler(handlerType, name="group_source_{}_{}".format(handlerType, grouperType),
                                groupingPolicy=groupPolicy)

    testGroups = []
    for source in range(2):
        externalId = None
        if grouperType == 1:
            externalId = 146
        testGroups.append(TestGroup(handler, ["./data/girl_{}_{}.jpg".format(1, j) for j in range(2)],
                                    externalId=externalId, countImgForTestPrepare=1, source=source))

    case = GroupHandlerTestCase(handler, testGroups,
                                "test_handlers_group_source_{}_{}".format(handlerType, grouperType))
    return case


def group_generator_test_handlers_group_tags(handlerType, grouperType):
    groupPolicy = generateBaseGroupPolicy(grouperType)
    handler = createTestHandler(handlerType,
                                name="group_source_tags_{}_{}".format(handlerType, grouperType),
                                groupingPolicy=groupPolicy)
    externalId = None
    if grouperType == 1:
        externalId = 146
    testGroups = [TestGroup(handler, ["./data/girl_{}_{}.jpg".format(1, j) for j in range(3)],
                            externalId=externalId) for countGroup in range(2)]

    case = GroupHandlerTestCase(handler, testGroups,
                                "test_handlers_group_tags_{}_{}".format(handlerType, grouperType))
    return case


def group_generator_test_handlers_group_person_attach_simple(handlerType):
    groupPolicy = generateBaseGroupPolicy()
    groupPolicy["create_person_policy"] = {"create_person": 1,
                                           "attach_policy": [
                                               {"list_id": BaseTestsHandlersPolicies.personsAttachLists[0]}]}

    handler = createTestHandler(handlerType, name="group_person_attach_simple",
                                groupingPolicy=groupPolicy)
    testGroup = TestGroup(handler, ["./data/girl_1_1.jpg"], externalId=146,
                          personsLists=[BaseTestsHandlersPolicies.personsAttachLists[0]])

    case = GroupHandlerTestCase(handler, [testGroup],
                                "test_handlers_group_person_attach_simple_{}".format(handlerType))
    return case


def group_generator_test_handlers_group_person_attach_policy_with_one_filter(handlerType):
    groupPolicy = generateBaseGroupPolicy()
    groupPolicy["create_person_policy"] = {
        "create_person": 1,
        "attach_policy": [
            {
                "list_id": BaseTestsHandlersPolicies.personsAttachLists[0],
                "filters": {"gender": 1}
            },
            {
                "list_id": BaseTestsHandlersPolicies.personsAttachLists[1],
                "filters": {"age_range": {"start": 30, "end": 100}}
            }
        ]
    }

    simFilter = {
        "list_id": BaseTestsHandlersPolicies.personsAttachLists[2],
        "filters":
            {
                "similarity_filter":
                    {
                        "policy": 1,
                        "lists": [{
                            "list_id": matchingList,
                            "threshold": 0.8
                        } for matchingList in BaseTestsHandlersPolicies.personsMatchingLists]
                    }
            }
    }
    if handlerType == "search":
        groupPolicy["create_person_policy"]["attach_policy"].append(simFilter)

    handler = createTestHandler(handlerType, name="group_person_attach_policy_with_one_filter",
                                groupingPolicy=groupPolicy)

    testGroup1 = TestGroup(handler, ["./data/man_young.jpg"], externalId=146,
                           personsLists=[BaseTestsHandlersPolicies.personsAttachLists[0]])
    testGroup2 = TestGroup(handler, ["./data/girl_old.jpg"], externalId=147,
                           personsLists=[BaseTestsHandlersPolicies.personsAttachLists[1]])
    testGroup3 = TestGroup(handler, ["./data/girl_young.jpg"], externalId=148,
                           personsLists=[])
    testGroups = [testGroup1, testGroup2, testGroup3]

    if handlerType == "search":
        testGroups.append(TestGroup(handler, ["./data/girl_1_2.jpg"], externalId=149,
                                    personsLists=[BaseTestsHandlersPolicies.personsAttachLists[2]]))
        testGroups.append(TestGroup(handler, ["./data/man_old.jpg"], externalId=150,
                                    personsLists=[BaseTestsHandlersPolicies.personsAttachLists[0],
                                                  BaseTestsHandlersPolicies.personsAttachLists[1]]))
    case = GroupHandlerTestCase(handler, testGroups,
                                "test_handlers_group_person_attach_policy_with_one_filter_{}".format(handlerType))
    return case


def group_generator_test_handlers_group_person_attach_with_several_filters(handlerType):
    groupPolicy = generateBaseGroupPolicy()
    groupPolicy["create_person_policy"] = {
        "create_person": 1,
        "attach_policy": [
            {
                "list_id": BaseTestsHandlersPolicies.personsAttachLists[0],
                "filters": {"gender": 0}
            },
            {
                "list_id": BaseTestsHandlersPolicies.personsAttachLists[1],
                "filters": {"age_range": {"start": 30, "end": 100},
                            "gender": 0}
            }
        ]
    }

    simFilter = {
        "list_id": BaseTestsHandlersPolicies.personsAttachLists[2],
        "filters":
            {
                "gender": 0,
                "age_range": {"start": 16, "end": 100},
                "similarity_filter":
                    {
                        "policy": 1,
                        "lists": [{
                            "list_id": matchingList,
                            "threshold": 0.98
                        } for matchingList in BaseTestsHandlersPolicies.personsMatchingLists]
                    }
            }
    }

    if handlerType == "search":
        groupPolicy["create_person_policy"]["attach_policy"].append(simFilter)

    handler = createTestHandler(handlerType, name="person_attach_with_several_filters",
                                groupingPolicy=groupPolicy)

    testGroup1 = TestGroup(handler, ["./data/girl_young.jpg"], externalId=146,
                           personsLists=[BaseTestsHandlersPolicies.personsAttachLists[0]])
    testGroup2 = TestGroup(handler, ["./data/man_old.jpg"], externalId=147,
                           personsLists=[])

    testGroups = [testGroup1, testGroup2]
    if handlerType == "search":
        testGroups.append(TestGroup(handler, ["./data/girl_old.jpg"], externalId=149,
                                    personsLists=[BaseTestsHandlersPolicies.personsAttachLists[0],
                                                  BaseTestsHandlersPolicies.personsAttachLists[1]]))
        testGroups.append(TestGroup(handler, ["./data/girl_1_0.jpg"], externalId=150,
                                    personsLists=[BaseTestsHandlersPolicies.personsAttachLists[0],
                                                  BaseTestsHandlersPolicies.personsAttachLists[2]]))
    case = GroupHandlerTestCase(handler, testGroups,
                                "test_handlers_group_person_attach_with_several_filters_{}".format(handlerType))
    return case


def group_generator_test_handlers_group_attach_group_to_non_exist_persons_list():
    groupPolicy = {
        "ttl": 10,
        "grouper": 1,
        "threshold": 0.3,
        "create_person_policy": {
            "create_person": 1,
            "attach_policy": [
                {"list_id": str(uuid.uuid4())}
            ]
        }
    }
    handler = createTestHandler("extract", name="person_attach_with_several_filters",
                                groupingPolicy=groupPolicy)

    testGroup = TestGroup(handler, ["./data/man_old.jpg"], externalId=147,
                          personsLists=[])

    case = GroupHandlerTestCase(handler, [testGroup],
                                "test_handlers_group_attach_group_to_non_exist_persons_list")
    return case


def group_generator_test_handlers_group_create_person_from_group_with_attaching_descriptor():
    groupPolicy = {
        "ttl": 10,
        "grouper": 1,
        "threshold": 0.3,
        "create_person_policy": {
            "create_person": 1,
        }
    }
    handler = createTestHandler("extract", name="person_attach_with_several_filters",
                                groupingPolicy=groupPolicy)

    testGroup = TestGroup(handler, ["./data/man_old.jpg"], externalId=147,
                          personsLists=[])

    case = GroupHandlerTestCase(handler, [testGroup],
                                "test_handlers_group_attach_group_to_non_exist_persons_list")
    return case


cases = {
    "test_handlers_group_simple_policy":
        {"TestGroupsGenerator": lambda: [group_generator_test_handlers_group_simple_policy(handlerType, grouper) for
                                         grouper in range(1, 3) for handlerType in ["extract", "search"]]},
    "test_handlers_group_search_aggregator":
        {"TestGroupsGenerator": lambda: [group_generator_test_handlers_group_search_aggregator(lunaList, searchType)
                                         for lunaList in [createBigList()] for searchType in range(1, 4)]
         },
    "test_handlers_group_gender_aggregator":
        {"TestGroupsGenerator": lambda: [group_generator_test_handlers_group_gender_aggregator(handlerType, genderType)
                                         for handlerType in ["extract", "search"] for genderType in range(1, 3)]
         },
    "test_handlers_group_age_aggregator":
        {"TestGroupsGenerator": lambda: [group_generator_test_handlers_group_age_aggregator(handlerType) for handlerType
                                         in ["extract", "search"]]
         },
    "test_handlers_group_simple_create_person":
        {"TestGroupsGenerator": lambda: [group_generator_test_handlers_group_simple_create_person(handlerType)
                                         for handlerType in ["extract", "search"]]
         },
    "test_handlers_group_create_person_with_one_filters":
        {"TestGroupsGenerator": lambda: [group_generator_test_handlers_group_create_person_with_one_filters(handlerType,
                                                                                                            filterType)
                                         for handlerType in ["extract", "search"] for filterType in range(3) if
                                         handlerType != "extract" or filterType != 2]
         },
    "test_handlers_group_create_person_with_several_filters":
        {"TestGroupsGenerator": lambda: [
            group_generator_test_handlers_group_create_person_with_several_filters(handlerType) for handlerType in
            ["extract", "search"]]
         },
    "test_handlers_group_source":
        {"TestGroupsGenerator": lambda: [group_generator_test_handlers_group_source(handlerType, grouper) for
                                         grouper in range(1, 3) for handlerType in ["extract", "search"]]
         },
    "test_handlers_group_person_attach_simple":
        {"TestGroupsGenerator": lambda: [group_generator_test_handlers_group_person_attach_simple(handlerType) for
                                         handlerType in ["extract", "search"]]
         },
    "test_handlers_group_person_attach_policy_with_one_filter":
        {"TestGroupsGenerator": lambda: [
            group_generator_test_handlers_group_person_attach_policy_with_one_filter(handlerType) for
            handlerType in ["extract", "search"]]
         },
    "test_handlers_group_person_attach_with_several_filters":
        {"TestGroupsGenerator": lambda: [
            group_generator_test_handlers_group_person_attach_with_several_filters(handlerType) for
            handlerType in ["extract", "search"]]
         },
    "test_handlers_group_attach_group_to_non_exist_persons_list":
        {"TestGroupsGenerator": lambda: [
            group_generator_test_handlers_group_attach_group_to_non_exist_persons_list()]
         }
}
