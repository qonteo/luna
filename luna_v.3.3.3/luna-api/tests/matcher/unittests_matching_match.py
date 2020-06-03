from crutches_on_wheels.errors.errors import Error
from tests.classes import authStr
from tests.matcher.matcher_caseGenerator import CaseGenerator
from tests.matcher.unittests_abstract_match import TestAbstractMatching
from tests import luna_api_functions


class TestMatchingMatch(TestAbstractMatching):
    """
    Tests of matching match
    """

    resource = '/matching/match'

    def test_matching_match_descriptor_vs_list_descriptors(self):
        """
        .. test:: test_matching_match_descriptor_vs_list_descriptors

            :resources: "/matching/match"
            :description: success matching descriptor vs list of descriptors
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def matchDescriptorsTest(headers, auth):
            listId = self.descriptorsListId
            photoId = self.photoId
            reply = luna_api_functions.match(headers, listId=listId, descriptorId=photoId)
            self.assertSuccessMatching(reply, authStr(auth), False)
            self.assertEqual(len(reply.body["candidates"]), 3, authStr(auth))

        matchDescriptorsTest()

    def test_matching_match_person_vs_list_descriptors(self):
        """
        .. test:: test_matching_match_person_vs_list_descriptors

            :resources: "/matching/match"
            :description: success matching person vs list of descriptors
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def matchDescriptorsTest(headers, auth):
            listId = self.descriptorsListId
            personId = self.personId
            reply = luna_api_functions.match(headers, listId=listId, personId=personId)
            self.assertSuccessMatching(reply, authStr(auth), False)
            self.assertEqual(len(reply.body["candidates"]), 3, authStr(auth))

        matchDescriptorsTest()

    def test_matching_match_limit_params(self):
        """
        .. test:: test_matching_match_limit_params

            :resources: "/matching/match"
            :description: testing of valid values of 'limit' param
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def limitParamsTest(headers, auth):
            queryParams = {
                "query": {"person_id": self.personId, "list_id": self.descriptorsListId},
                "isPerson": False
            }
            self.limitParamsTest(headers, auth, queryParams)

        limitParamsTest()

    def test_matching_match_with_invalid_limit_params(self):
        """
        .. test:: test_matching_match_with_invalid_limit_params

            :resources: "/matching/match"
            :description: testing of invalid values of 'limit' param
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def limitParamsTest(headers, auth):
            queryParams = {"person_id": self.personId, "list_id": self.descriptorsListId}
            self.invalidLimitParamsTest(headers, auth, queryParams)
        limitParamsTest()

    def test_matching_match_bad_id_query_param(self):
        """
        .. test:: test_matching_match_bad_id_query_param

            :resources: "/matching/match"
            :description: failed matching match with bad type of query params
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def matchingBadIdQueryParamTest(headers, auth):
            testCases = CaseGenerator.badIdQueryParamsTestSuiteMatcherGenerator(
                self.descriptorsListId, self.photoId, 1)

            self.matchingBadIdQueryParams(headers, auth, testCases)

        matchingBadIdQueryParamTest()

    def test_matching_match_non_exist_id(self):
        """
        .. test:: test_matching_match_non_exist_id

            :resources: "/matching/match"
            :description: trying to match with non exist id value (uuid4)
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def matchingNonExistIdTest(headers, auth):
            testCases = (
                {
                    "queries": {"list_id": self.descriptorsListId},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["person_id", "descriptor_id"])]
                },
                {
                    "queries": {"descriptor_ids": self.dynamicDescriptorsList},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["person_id", "descriptor_id"])]
                },
                {
                    "queries": {"descriptor_id": self.photoId},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["list_id", "descriptor_ids"])]
                },
                {
                    "queries": {"person_id": self.personId},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["list_id", "descriptor_ids"])]
                }
            )
            self.matchingNonExistIdTest(headers, auth, testCases)

        matchingNonExistIdTest()

    def test_matching_match_excess_query_params(self):
        """
        .. test:: test_matching_match_excess_query_params

            :resources: "/matching/match"
            :description: success match with too much query params (1 of query param is excess)
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchingExcessTest(headers, auth):
            testCases = (
                    {"person_id": self.personId,
                     "descriptor_ids": self.dynamicDescriptorsList,
                     "list_id": self.descriptorsListId},
                    {"person_id": self.personId, "descriptor_id": self.photoId,
                     "list_id": self.descriptorsListId},
                )
            self.matchingExcessTest(headers, auth, testCases, False)

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
            queryParams = {"person_id": self.personWithoutPhoto, "list_id": self.descriptorsListId}
            self.matchEmptyPersonTest(headers, auth, queryParams)

        matchEmptyPersonTest()

    def test_matching_match_not_consistent_query_params(self):
        """
        .. test:: test_matching_match_not_consistent_query_params

            :resources: "/matching/match"
            :description: trying to match with no full query params (one of necessary param is missing)
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchingNonConsistentTest(headers, auth):
            testCases = (
                {
                    "queries": {"list_id": self.descriptorsListId},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["person_id", "descriptor_id"])]
                },
                {
                    "queries": {"descriptor_ids": self.dynamicDescriptorsList},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["person_id", "descriptor_id"])]
                },
                {
                    "queries": {"descriptor_id": self.photoId},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["list_id", "descriptor_ids"])]
                },
                {
                    "queries": {"person_id": self.personId},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [(["list_id", "descriptor_ids"])]
                }
            )
            self.matchingNonConsistentTest(headers, auth, testCases)

        matchingNonConsistentTest()

    def test_matching_match_empty_list(self):
        """
        .. test:: test_matching_match_empty_list

            :resources: "/matching/match"
            :description: success matching with list which has no id
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchEmptyListTest(headers, auth):
            emptyDescriptorListId = self.createList(headers, isPersonList=False)
            testCases = ({"query": {"descriptor_id": self.photoId, "list_id": emptyDescriptorListId},
                           "isPersons": False},)
            self.matchEmptyListTest(headers, auth, testCases)

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
            badDescriptorIds = (self.dynamicDescriptorsList[0], self.nonExistsId)
            testCases = ({
                "queries": {"descriptor_id": self.photoId, "descriptor_ids": badDescriptorIds},
                "error": Error.ObjectNotFound,
                "msgFormat": ["descriptors"]
            },)
            self.matchNonExistItemListTest(headers, auth, testCases)

        matchNonExistItemListTest()