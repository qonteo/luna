from tests.system_tests.base_test_handlers_logic import *
from tests.system_tests.group_tests_cases import group_generator_test_handlers_group_mixed_policy, cases, group_generator_test_handlers_group_ttl, group_generator_test_handlers_group_tags, group_generator_test_handlers_group_create_person_from_group_with_attaching_descriptor


def checkGroupGender(test, genderAggregator, group):
    gendersEvents = []
    for descriptor in group["descriptors"]:
        event = getEvent(descriptor).json
        gendersEvents.append(event["extract"]["attributes"]["gender"])
        test.assertEqual(event["group_id"], group["id"])

    gender = group["attributes"]["gender"]

    if genderAggregator == 2:
        eventsGender = 0
        for genderValue in gendersEvents:
            eventsGender += genderValue
        eventsGender = eventsGender / len(gendersEvents)
    else:
        eventsGender = mean = 0.5
        deviation = 0
        for genderValue in gendersEvents:
            dev = abs(mean - genderValue)
            if dev > deviation:
                deviation = dev
                eventsGender = genderValue
    test.assertAlmostEqual(eventsGender, gender, 5)


def checkGroupSearch(test, aggregator, group):
    groupEvents = []
    for descriptor in group["descriptors"]:
        event = getEvent(descriptor).json
        groupEvents.append(event)
        test.assertEqual(event["group_id"], group["id"])

    for candidate in group["search"]:
        cand_ = candidate["candidate"]
        id = cand_["person_id"] if "person_id" in cand_ else cand_["id"]
        similarity = cand_["similarity"]
        currentSimilarity = 0
        total = 0
        for event in groupEvents:
            for candidates in event["search"]:
                for cand in candidates["candidates"]:
                    if "person_id" in cand:
                        candId = cand["person_id"]
                    else:
                        candId = cand["id"]
                    if id == candId:
                        if aggregator == 1:
                            if currentSimilarity < cand["similarity"]:
                                currentSimilarity = cand["similarity"]
                        else:
                            currentSimilarity += cand["similarity"]
                            total += 1

        if aggregator == 1:
            test.assertEqual(currentSimilarity, similarity)
        elif aggregator == 2:
            test.assertAlmostEqual(currentSimilarity / total, similarity, 5)
        else:
            test.assertTrue(abs(similarity - currentSimilarity) > 0.000001)
            test.assertTrue(abs(similarity - currentSimilarity / total) > 0.000001)


def checkGroupAge(test, group):
    agesEvents = []
    for descriptor in group["descriptors"]:
        event = getEvent(descriptor).json
        agesEvents.append(event["extract"]["attributes"]["age"])
        test.assertEqual(event["group_id"], group["id"])

    gender = group["attributes"]["age"]

    eventsAge = 0
    for genderValue in agesEvents:
        eventsAge += genderValue
    eventsAge = int(eventsAge / len(agesEvents))

    test.assertEqual(eventsAge, gender)


class TestGroupPolicy(BaseTestsHandlersPolicies):
    TestGroupPolicyCurrentCases = {}
    RunningTests = []

    def __init__(self, *args, **kwargs):
        super(TestGroupPolicy, self).__init__(*args, **kwargs)
        if args[0] in cases:
            TestGroupPolicy.RunningTests.append(args[0])

    @classmethod
    def setUpClass(cls):
        super(TestGroupPolicy, cls).setUpClass()

        cls.superSetUpClass()

    @classmethod
    def superSetUpClass(cls):
        for testName in TestGroupPolicy.RunningTests:
            if testName in cases:
                testGroupsCases = cases[testName]["TestGroupsGenerator"]()
                TestGroupPolicy.TestGroupPolicyCurrentCases[testName] = testGroupsCases

        for testName, testCases in TestGroupPolicy.TestGroupPolicyCurrentCases.items():
            for groupHandlerTestCase in testCases:
                testingGroups = groupHandlerTestCase.groups

                for countEvent in range(10):
                    for testingGroup in testingGroups:
                        if testingGroup.countImgForTestPrepare > testingGroup.countSentEvents:
                            testingGroup.emitEvent()
        time.sleep(10)
        for testName, testCases in TestGroupPolicy.TestGroupPolicyCurrentCases.items():
            for groupHandlerTestCase in testCases:
                BaseTestsHandlersPolicies.emitNeutralImg("./data/man_old.jpg", groupHandlerTestCase.handler["id"])
        time.sleep(2)

    def test_handlers_group_simple_policy(self):

        def test(testingGroups):

            self.assertTrue(testingGroups[0].groupId != testingGroups[1].groupId)

            for testingGroup in testingGroups:
                queryParams = testingGroup.generateQueryParams()
                reply = emitEvent(testingGroups[0].handler["id"], testingGroup.imgsForGroup[0], queryParams)
                newGroupId = reply.json["events"][0]["group_id"]
                self.assertTrue(newGroupId != testingGroup.groupId, testingGroups[0].handler["name"])
                reply = getGroup(testingGroup.groupId)
                self.validateGroup(reply, testingGroups[0].handler, testingGroup.events)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases["test_handlers_group_simple_policy"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.groups)

    def test_handlers_group_mixed_policy(self):

        def test(testingGroups):
            self.uploadGroups(testingGroups, 2)

            self.assertTrue(testingGroups[0].groupId != testingGroups[1].groupId)
            self.assertTrue(testingGroups[2].groupId != testingGroups[1].groupId)
            self.assertTrue(testingGroups[0].groupId != testingGroups[2].groupId)
            eventsInMixedGroup = testingGroups[0].events + testingGroups[1].events
            newGroupId = None
            for count, testingGroup in enumerate(testingGroups):
                queryParams = testingGroup.generateQueryParams()
                reply = emitEvent(testingGroups[0].handler["id"], testingGroup.imgsForGroup[-1], queryParams)
                groupId = reply.json["events"][0]["group_id"]
                if count == 0:
                    newGroupId = groupId
                    eventsInMixedGroup.append(reply.json["events"][0]["id"])
                    self.assertTrue(groupId not in [testingGroups[0].groupId,
                                                    testingGroups[1].groupId], testingGroups[0].handler["name"])
                elif count == 1:
                    eventsInMixedGroup.append(reply.json["events"][0]["id"])
                    self.assertEqual(groupId, reply.json["events"][0]["group_id"])
                else:
                    self.assertEqual(groupId, testingGroup.groupId, testingGroups[0].handler["name"])
            time.sleep(2)

            groupReply = getGroup(newGroupId)
            self.validateGroup(groupReply, testingGroups[0].handler, eventsInMixedGroup)
            for testingGroup in testingGroups[:-1]:
                groupReply = getGroup(testingGroup.groupId)
                self.assertEqual(404, groupReply.statusCode)

        for handlerType in ["extract", "search"]:
            with self.subTest(handlerType=handlerType):
                testCase = group_generator_test_handlers_group_mixed_policy(handlerType)
                test(testCase.groups)

    def test_handlers_group_search_aggregator(self):

        def test(testingGroups, handlerForTest, searchAggregator):

            for count, testingGroup in enumerate(testingGroups):
                groupReply = getGroup(testingGroup.groupId)
                self.validateGroup(groupReply, handlerForTest, testingGroup.events)
                self.assertTrue(len(groupReply.json["search"][0]["candidate"]) > 0)
                checkGroupSearch(self, searchAggregator, groupReply.json)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases["test_handlers_group_search_aggregator"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.groups, subCase.handler, subCase.searchType)

    def test_handlers_group_gender_aggregator(self):

        def test(testingGroups, genderAggregator, handlerForTest):

            for testingGroup in testingGroups:
                groupReply = getGroup(testingGroup.groupId)
                self.validateGroup(groupReply, handlerForTest, testingGroup.events)

                checkGroupGender(self, genderAggregator, groupReply.json)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases["test_handlers_group_gender_aggregator"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.groups, subCase.genderAggregatorType, subCase.handler)

    def test_handlers_group_age_aggregator(self):

        def test(testingGroups, handlerForTest):

            for testingGroup in testingGroups:
                groupReply = getGroup(testingGroup.groupId)
                self.validateGroup(groupReply, handlerForTest, testingGroup.events)

                checkGroupAge(self, groupReply.json)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases["test_handlers_group_age_aggregator"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.groups, subCase.handler)

    def test_handlers_group_simple_create_person(self):

        def test(testingGroups, handlerForTest):
            self.validateGroups(testingGroups, handlerForTest)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases["test_handlers_group_simple_create_person"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.groups, subCase.handler)

    def test_handlers_group_create_person_with_one_filters(self):
        def test(handlerForTest, testingGroups):

            for countGroup, testingGroup in enumerate(testingGroups):
                groupReply = getGroup(testingGroup.groupId)
                if not testingGroup.createPerson:
                    self.assertTrue(groupReply.json["person_id"] is None)
                self.validateGroup(groupReply, handlerForTest, testingGroup.events,
                                   checkPerson=testingGroup.createPerson)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases[
            "test_handlers_group_create_person_with_one_filters"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.handler, subCase.groups)

    def test_handlers_group_create_person_with_several_filters(self):

        def test(testingGroups, handlerForTest):

            for countGroup, testingGroup in enumerate(testingGroups):
                groupReply = getGroup(testingGroup.groupId)
                if not testingGroup.createPerson:
                    self.assertTrue(groupReply.json["person_id"] is None)
                self.validateGroup(groupReply, handlerForTest, testingGroup.events,
                                   checkPerson=testingGroup.createPerson)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases[
            "test_handlers_group_create_person_with_several_filters"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.groups, subCase.handler)

    def test_handlers_group_ttl(self):

        def test(testingGroups, handlerForTest):
            for testingGroup in testingGroups:
                queryParams = testingGroup.generateQueryParams()
                reply = emitEvent(handlerForTest["id"], testingGroup.imgsForGroup[0], queryParams)
                groupId = reply.json["events"][0]["group_id"]

                self.assertEqual(groupId, testingGroup.groupId, handlerForTest["name"])
                testingGroup.events.append(reply.json["events"][0]["id"])

            self.validateGroups(testingGroups, handlerForTest)

        casesTTL = []

        for grouperType in range(1, 3):
            for handlerType in ["extract", "search"]:
                case = group_generator_test_handlers_group_ttl(handlerType, grouperType)
                self.uploadGroups(case.groups, case.groups[0].countImgForTestPrepare)
                casesTTL.append(case)
        start = time.time()
        time.sleep(5)

        for case in casesTTL:
            with self.subTest(subCase=case.description):
                test(case.groups, case.handler)

        time.sleep(11 - (time.time() - start))

        for case in casesTTL:
            with self.subTest(subCase=case.description):
                test(case.groups, case.handler)

    def test_handlers_group_source(self):
        def test(testingGroups, handlerForTest):
            self.assertTrue(testingGroups[0].groupId != testingGroups[1].groupId)
            self.validateGroups(testingGroups, handlerForTest)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases["test_handlers_group_source"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.groups, subCase.handler)

    def test_handlers_group_tags(self):
        def test(testingGroups, countEventsForGroup):
            for countEvent in range(countEventsForGroup):
                for testingGroup in testingGroups:
                    queryParams = testingGroup.generateQueryParams()
                    queryParams["tags"] = "beer_{}".format(countEvent % 2)
                    emitEvent(testingGroup.handler["id"], testingGroup.imgsForGroup[testingGroup.countSentEvents],
                              queryParams)
                    testingGroup.emitEvent()

            for testingGroup in testingGroups:
                reply = getGroup(testingGroup.groupId)
                self.assertEqual(set(reply.json["tags"]), set(["beer_{}".format(i) for i in range(2)]))

        for grouperType in range(1, 3):
            for handlerType in ["extract", "search"]:
                with self.subTest(handlerType=handlerType):
                    with self.subTest(grouperType=grouperType):
                        case = group_generator_test_handlers_group_tags(handlerType, grouperType)
                        test(case.groups, 3)

    def test_handlers_group_person_attach_simple(self):

        def test(testingGroup, handlerForTest):
            reply = getGroup(testingGroup.groupId)
            self.validateGroup(reply, handlerForTest, testingGroup.events, checkPerson=True,
                               personsLists=testingGroup.personsLists)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases["test_handlers_group_person_attach_simple"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.groups[0], subCase.handler)

    def test_handlers_group_person_attach_policy_with_one_filter(self):
        def test(testingGroups, handlerForTest):

            for testingGroup in testingGroups:
                reply = getGroup(testingGroup.groupId)
                self.validateGroup(reply, handlerForTest, testingGroup.events, checkPerson=True,
                                   personsLists=testingGroup.personsLists)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases[
            "test_handlers_group_person_attach_policy_with_one_filter"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.groups, subCase.handler)

    def test_handlers_group_person_attach_with_several_filters(self):
        def test(testingGroups, handlerForTest):

            for testingGroup in testingGroups:
                reply = getGroup(testingGroup.groupId)
                self.validateGroup(reply, handlerForTest, testingGroup.events, checkPerson=True,
                                   personsLists=testingGroup.personsLists)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases[
            "test_handlers_group_person_attach_with_several_filters"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.groups, subCase.handler)

    def test_handlers_group_create_person_from_group_with_attaching_descriptor(self):

        def test(testingGroups, handlerForTest):
            self.uploadGroups(testingGroups, 1)
            for testingGroup in testingGroups:
                descriptorId = testingGroup.events[0]
                personId = TestGroupPolicy.lunaClient.createPerson(
                    userData="create_person_from_group_with_attaching_descriptor",
                    raiseError=True).body["person_id"]
                BaseTestsHandlersPolicies.personsToDelete.append(personId)
                TestGroupPolicy.lunaClient.linkDescriptorToPerson(personId, descriptorId, raiseError=True)
                BaseTestsHandlersPolicies.closeGroupsOfhandler("./data/girl_young.jpg", testingGroup.handler["id"])
                reply = getGroup(testingGroup.groupId)
                self.validateGroup(reply, handlerForTest, testingGroup.events, checkPerson=False,
                                   withoutError=False)
                self.assertTrue(reply.json["error"]["detail"].find("error_code: 11016") > 0)

        case = group_generator_test_handlers_group_create_person_from_group_with_attaching_descriptor()
        test(case.groups, case.handler)

    def test_handlers_group_attach_group_to_non_exist_persons_list(self):
        def test(testingGroups, handlerForTest):
            for testingGroup in testingGroups:
                reply = getGroup(testingGroup.groupId)
                self.validateGroup(reply, handlerForTest, testingGroup.events, checkPerson=True,
                                   personsLists=testingGroup.personsLists, withoutError=False)
                self.assertTrue(reply.json["error"]["detail"].find("error_code: 22003") > 0)

        for subCase in TestGroupPolicy.TestGroupPolicyCurrentCases[
            "test_handlers_group_attach_group_to_non_exist_persons_list"]:
            with self.subTest(subCase=subCase.description):
                test(subCase.groups, subCase.handler)
