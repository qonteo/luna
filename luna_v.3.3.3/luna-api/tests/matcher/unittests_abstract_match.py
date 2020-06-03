import uuid
from abc import ABCMeta
from crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase, authStr
from tests.resources import standardImage, onePersonList
from tests import luna_api_functions


class TestAbstractMatching(TestBase, metaclass=ABCMeta):

    def setUp(self):
        self.createAccountAndToken()

    personId = None                                     #: reference person id for matching
    photoId = None                                      #: reference descriptor id for matching
    personsListId = None                                #: persons list candidates for matching
    descriptorsListId = None                            #: descriptors list candidates for matching
    dynamicPersonsList = None                           #: list of persons for matching  as candidates
    dynamicDescriptorsList = None                       #: list of descriptors for matching as candidates
    nonExistsId = None
    personWithoutPhoto = None
    resource = None
    uploadImage = None
    isBinary = False
    isSetUp = False

    @classmethod
    def setUpClass(cls):
        if not TestAbstractMatching.isSetUp:
            luna_api_functions.registration()
            headers = luna_api_functions.createAuthHeader()

            TestAbstractMatching.photoId = \
                luna_api_functions.extractDescriptors(headers, filename=standardImage).body["faces"][0]["id"]
            TestAbstractMatching.personId = TestBase.createPersonWithPhoto(headers)
            TestAbstractMatching.personWithoutPhoto = TestBase.createPerson(headers)
            TestAbstractMatching.descriptorsListId, \
            TestAbstractMatching.personsListId, \
            TestAbstractMatching.dynamicDescriptorsList, \
            TestAbstractMatching.dynamicPersonsList = TestAbstractMatching.prepareCandidatesListsDataForTests()
            TestAbstractMatching.nonExistsId = str(uuid.uuid4())
            TestAbstractMatching.isSetUp = True

    @staticmethod
    def prepareCandidatesListsDataForTests():
        headers = luna_api_functions.createAuthHeader()
        descriptorsList = luna_api_functions.createList(headers, False,
                                                        "visionlabs,  matcing tests, descriptors lists").body["list_id"]
        personsList = luna_api_functions.createList(headers, True,
                                                    "visionlabs,  matcing tests, persons lists").body["list_id"]
        dynamicPersonsList = []
        dynamicDescriptorsList = []
        for photo in onePersonList:
            photoId = luna_api_functions.extractDescriptors(headers, filename=photo).body["faces"][0]["id"]
            dynamicDescriptorsList.append(photoId)
            luna_api_functions.linkListToDescriptor(headers, photoId, descriptorsList, 'attach')

            personId = luna_api_functions.createPerson(headers, userData='test user data',
                                                       externalId='test-external-id').body["person_id"]
            dynamicPersonsList.append(personId)
            luna_api_functions.linkListToPerson(headers, personId, personsList, "attach")
            luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")

        dynamicDescriptorsList = tuple(dynamicDescriptorsList)
        dynamicPersonsList = tuple(dynamicPersonsList)
        return descriptorsList, personsList, dynamicDescriptorsList, dynamicPersonsList

    def limitParamsTest(self, headers, auth, queryParams):

        limitParams = ({"limitValue": -1, "expectedCandidatesCount": 3},
                       {"limitValue": 0, "expectedCandidatesCount": 3},
                       {"limitValue": 1, "expectedCandidatesCount": 1},
                       {"limitValue": 5, "expectedCandidatesCount": 5},
                       {"limitValue": 6, "expectedCandidatesCount": 5})

        for limitParam in limitParams:
            with self.subTest(limitParam=limitParam):
                queryParams['query']['limit'] = str(limitParam['limitValue'])
                reply = luna_api_functions.manualRequest(self.resource, 'POST', queryParams=queryParams['query'],
                                                         body=self.uploadImage, headers=headers, isBinary=self.isBinary)
            self.assertSuccessMatching(reply, authStr(auth), queryParams['isPerson'])
            self.assertEqual(len(reply.body["candidates"]), limitParam['expectedCandidatesCount'])

    def invalidLimitParamsTest(self, headers, auth, queryParams):
        invalidLimitParams = ("rwwerw", "", [])
        for invalidLimitParam in invalidLimitParams:
            with self.subTest(invalidLimitParam=invalidLimitParam):
                queryParams['limit'] = invalidLimitParam
                reply = luna_api_functions.manualRequest(self.resource, 'POST', queryParams=queryParams,
                                                         headers=headers)
                self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams, msgFormat=["limit"], auth=authStr(auth))

    def matchEmptyPersonTest(self, headers, auth, queryParams):
        reply = luna_api_functions.manualRequest(self.resource, 'POST', queryParams=queryParams, headers=headers)
        self.assertSuccessMatching(reply, authStr(auth))
        self.assertEqual(len(reply.body["candidates"]), 0, authStr(auth))

    def matchingNonConsistentTest(self, headers, auth, testCases):
        for testCase in testCases:
            with self.subTest(testCase=testCases):
                queryParams = testCase["queries"]
                errorInfo = testCase["error"]
                msgFormat = testCase["msgFormat"]
                with self.subTest(queryParams=queryParams):
                    reply = luna_api_functions.manualRequest(self.resource, 'POST', queryParams=queryParams,
                                                             body=self.uploadImage, headers=headers,
                                                             isBinary=self.isBinary)
                    self.assertErrorRestAnswer(reply, 400, errorInfo, msgFormat=msgFormat, auth=authStr(auth))

    def matchEmptyListTest(self, headers, auth, testCases):
        for testCase in testCases:
            with self.subTest(testCase=testCase):
                reply = luna_api_functions.manualRequest(self.resource, 'POST', queryParams=testCase["query"],
                                                         body=self.uploadImage, headers=headers, isBinary=self.isBinary)
                self.assertSuccessMatching(reply, authStr(auth), isPersons=testCase['isPersons'])
                self.assertEqual(len(reply.body["candidates"]), 0, authStr(auth))

    def matchNonExistItemListTest(self, headers, auth, testCases):
        for testCase in testCases:
            with self.subTest(testCase=testCase):
                reply = luna_api_functions.manualRequest(self.resource, 'POST', queryParams=testCase["queries"],
                                                         body=self.uploadImage, headers=headers, isBinary=self.isBinary)
                self.assertErrorRestAnswer(reply, 400, testCase["error"], auth=authStr(auth),
                                           msgFormat=testCase["msgFormat"])

    def matchingNonExistIdTest(self, headers, auth, testCases):
        for testCase in testCases:
            with self.subTest(testCase=testCase):
                queryParams = testCase["queries"]
                errorInfo = testCase["error"]
                msgFormat = testCase["msgFormat"]
                headers["Content-Type"] = "image/jpeg"
                reply = luna_api_functions.manualRequest(self.resource, 'POST', queryParams=queryParams,
                                                         body=self.uploadImage, headers=headers, isBinary=self.isBinary)
                self.assertErrorRestAnswer(reply, 400, errorInfo, msgFormat=msgFormat, auth=authStr(auth))

    def matchingExcessTest(self, headers, auth, testCases, isPersons):
        for testCase in testCases:
            with self.subTest(testCase=testCase):
                reply = luna_api_functions.manualRequest(self.resource, 'POST', queryParams=testCase, headers=headers,
                                                         body=self.uploadImage, isBinary=self.isBinary)
                self.assertEqual(reply.statusCode, 201, authStr(auth))
                self.assertSuccessMatching(reply, authStr(auth), isPersons)

    def matchingBadIdQueryParams(self, headers, auth, testCases):
        for testCase in testCases:
            with self.subTest(testCase=testCase):
                queryParams = testCase["queries"]
                msgFormat = testCase['msgFormat']
                reply = luna_api_functions.manualRequest(self.resource, 'POST', queryParams=queryParams,
                                                         body=self.uploadImage, headers=headers, isBinary=self.isBinary)
                self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams, msgFormat=msgFormat, auth=authStr(auth))
