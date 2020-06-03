from crutches_on_wheels.errors.errors import Error
from tests.classes import authStr
from tests.matcher.matcher_caseGenerator import CaseGenerator
from tests.matcher.unittests_abstract_match import TestAbstractMatching
from tests import luna_api_functions


class TestMatchingIdentify(TestAbstractMatching):
    """
    Tests of matching identify
    """

    resource = '/matching/identify'

    def setUp(self):
        self.createAccountAndToken()

    def test_matching_identify_descriptor_vs_list(self):
        """
        .. test:: test_matching_identify_descriptor_vs_list

            :resources: "/matching/identify"
            :description: success matching descriptor vs list of persons
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def descriptorVsListTest(headers, auth):
            listId = self.personsListId
            reply = luna_api_functions.identify(headers, listId=listId, descriptorId=self.photoId)
            self.assertSuccessMatching(reply, authStr(auth))
            self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))

        descriptorVsListTest()

    def test_matching_identify_descriptor_vs_dynamic_list_persons(self):
        """
        .. test:: test_matching_identify_descriptor_vs_dynamic_list_persons

            :resources: "/matching/identify"
            :description: success matching descriptor vs dynamic list of persons
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchDescriptorVSListPerson(headers, auth):
            personIds = self.dynamicPersonsList
            photoId = self.photoId
            reply = luna_api_functions.identify(headers, personIds=personIds, descriptorId=photoId)
            self.assertSuccessMatching(reply, authStr(auth))
            self.assertEqual(reply.statusCode, 201, authStr(auth))

        matchDescriptorVSListPerson()

    def test_matching_identify_person_vs_list(self):
        """
        .. test:: test_matching_identify_person_vs_list

            :resources: "/matching/identify"
            :description: success matching person vs list of persons
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def personVsListTest(headers, auth):
            listId = self.personsListId
            personId = self.personId
            reply = luna_api_functions.identify(headers, listId=listId, personId=personId)
            self.assertSuccessMatching(reply, authStr(auth))
            self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))

        personVsListTest()

    def test_matching_identify_person_vs_dynamic_list_persons(self):
        """
        .. test:: test_matching_identify_person_vs_dynamic_list_persons

            :resources: "/matching/identify"
            :description: success matching person vs dynamic list of persons
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchPersonVSListPerson(headers, auth):
            personIds = self.dynamicPersonsList
            personId = self.personId
            reply = luna_api_functions.identify(headers, personIds=personIds, personId=personId)
            self.assertSuccessMatching(reply, authStr(auth))

        matchPersonVSListPerson()

    def test_matching_identify_limit_params(self):
        """
        .. test:: test_matching_identify_limit_params

            :resources: "/matching/identify"
            :description: testing of valid values of 'limit' param
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def limitParamsTest(headers, auth):
            queryParams = {"query": {
                "person_id": self.personId, "list_id": self.personsListId},
                "isPerson": True
            }
            self.limitParamsTest(headers, auth, queryParams)
        limitParamsTest()

    def test_matching_identify_with_invalid_limit_params(self):
        """
        .. test:: test_matching_identify_with_invalid_limit_params

            :resources: "/matching/identify"
            :description: testing of invalid values of 'limit' param
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def invalidlimitParamsTest(headers, auth):
            queryParams = {"person_id": self.personId, "list_id": self.personsListId}
            self.invalidLimitParamsTest(headers, auth, queryParams)

        invalidlimitParamsTest()

    def test_matching_identify_bad_id_query_param(self):
        """
        .. test:: test_matching_identify_bad_id_query_param

            :resources: "/matching/identify"
            :description: failed matching identify with bad type of query params
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def matchingBadIdQueryParamTest(headers, auth):
            testCases = CaseGenerator.badIdQueryParamsTestSuiteIdentifierGenerator(
                self.personsListId, self.photoId, 1
            )

            self.matchingBadIdQueryParams(headers, auth, testCases)

        matchingBadIdQueryParamTest()

    def test_matching_identify_non_exist_id(self):
        """
        .. test:: test_matching_identify_non_exist_id

            :resources: "/matching/identify"
            :description: trying to match with non exist id value (uuid4)
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def matchingNonExistIdTest(headers, auth):
            testCases = (
                {
                    "queries": {"list_id": self.personsListId, "person_id": self.nonExistsId},
                    "error": Error.PersonNotFound,
                    "msgFormat": None
                },
                {
                    "queries": {"list_id": self.personsListId, "descriptor_id": self.nonExistsId},
                    "error": Error.DescriptorNotFound,
                    "msgFormat": None
                },
                {
                    "queries": {"descriptor_id": self.photoId, "list_id": self.nonExistsId},
                    "error": Error.ListNotFound,
                    "msgFormat": None
                },
                {
                    "queries": {"descriptor_id": self.photoId, "person_ids": self.nonExistsId},
                    "error": Error.ObjectNotFound,
                    "msgFormat": ["person"]
                }
            )
            self.matchingNonExistIdTest(headers, auth, testCases)

        matchingNonExistIdTest()

    def test_matching_identify_excess_query_params(self):
        """
        .. test:: test_matching_identify_excess_query_params

            :resources: "/matching/identify"
            :description: success match with too much query params (1 of query param is excess)
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchingExcessTest(headers, auth):
            testCases = (
                    {"person_id": self.personId, "person_ids": self.dynamicPersonsList,
                     "list_id": self.personsListId},
                    {"person_id": self.personId, "descriptor_id": self.photoId,
                     "list_id": self.personsListId},
                )
            self.matchingExcessTest(headers, auth, testCases, True)

        matchingExcessTest()

    def test_matching_identify_empty_person(self):
        """
        .. test:: test_matching_identify_empty_person

            :resources: "/matching/identify"
            :description: success matching person without descriptors vs list
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchEmptyPersonTest(headers, auth):
            queryParams = {"person_id": self.personWithoutPhoto, "list_id": self.personsListId}
            self.matchEmptyPersonTest(headers, auth, queryParams)

        matchEmptyPersonTest()

    def test_matching_identify_not_consistent_query_params(self):
        """
        .. test:: test_matching_not_consistent_query_params

            :resources: "/matching/identify"
            :description: trying to match with no full query params (one of necessary param is missing)
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchingNonConsistentTest(headers, auth):
            testCases = (
                {
                    "queries": {"list_id": self.personsListId},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["person_id", "descriptor_id"])]
                },
                {
                    "queries": {"person_ids": self.dynamicPersonsList},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["person_id", "descriptor_id"])]
                },
                {
                    "queries": {"descriptor_id": self.photoId},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["list_id", "person_ids"])]
                },
                {
                    "queries": {"person_id": self.personId},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["list_id", "person_ids"])]
                },
            )
            self.matchingNonConsistentTest(headers, auth, testCases)

        matchingNonConsistentTest()

    def test_matching_identify_empty_list(self):
        """
        .. test:: test_matching_identify_empty_list

            :resources: "/matching/identify"
            :description: success matching with list which has no id
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchEmptyListTest(headers, auth):
            emptyPersonListId = self.createList(headers, isPersonList=True)
            queryParams = ({"query": {"person_id": self.personId, "list_id": emptyPersonListId},
                            "isPersons": True},)
            self.matchEmptyListTest(headers, auth, queryParams)

        matchEmptyListTest()

    def test_matching_identify_one_of_list_id_non_exist(self):
        """
        .. test:: test_matching_identify_one_of_list_id_non_exist

            :resources: "/matching/identify"
            :description: trying to match with dynamic list where one of id doesn't exist
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchNonExistItemListTest(headers, auth):
            badPersonIds = (self.dynamicPersonsList[0], self.nonExistsId)
            testCase = ({
                "queries": {"descriptor_id": self.photoId, "person_ids": badPersonIds},
                "error": Error.ObjectNotFound,
                "msgFormat": ["person"]
            },)
            self.matchNonExistItemListTest(headers, auth, testCase)

        matchNonExistItemListTest()
