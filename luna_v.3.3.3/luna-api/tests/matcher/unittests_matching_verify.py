from crutches_on_wheels.errors.errors import Error
from tests.classes import authStr
from tests.matcher.matcher_caseGenerator import CaseGenerator
from tests.matcher.unittests_abstract_match import TestAbstractMatching
from tests.resources import onePersonList, standardImage
from tests import luna_api_functions


class TestMatchingVerify(TestAbstractMatching):
    """
    Tests of matching verify
    """


    resource = '/matching/verify'

    def setUp(self):
        self.createAccountAndToken()

    def test_matching_verify(self):
        """
        .. test:: test_matching_verify

            :resources: "/matching/verify"
            :description: success verifying request
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def verifyTest(headers, auth):
            personId = self.personId
            photoId = luna_api_functions.extractDescriptors(headers, filename=onePersonList[0]).body["faces"][0]["id"]
            reply = luna_api_functions.verify(headers, photoId, personId)
            self.assertResultMatching(reply.body["candidates"][0], authStr(auth))
            self.assertTrue(reply.body["candidates"][0]["person_id"] == personId, authStr(auth))

        verifyTest()

    def test_matching_verify_person_with_two_descriptors(self):
        """
        .. test:: test_matching_verify

            :resources: "/matching/verify"
            :description: success verifying of person with two_descriptors request (makes two request: before first
                          request person has 1 descriptor, before second request person has 2 descriptors, including
                          descriptor of verified photo)
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def verify2PhotoTest(headers, auth):
            personId = self.createPerson(headers)

            firstPhotoId1 = luna_api_functions.extractDescriptors(headers,
                                                                  filename=onePersonList[0]).body["faces"][0]["id"]
            luna_api_functions.linkDescriptorToPerson(headers, personId, firstPhotoId1, "attach")

            photoId = luna_api_functions.extractDescriptors(headers, filename=standardImage).body["faces"][0]["id"]
            reply = luna_api_functions.verify(headers, photoId, personId)
            self.assertResultMatching(reply.body["candidates"][0], authStr(auth))
            self.assertTrue(reply.body["candidates"][0]["person_id"] == personId, authStr(auth))
            sim = reply.body["candidates"][0]["similarity"]

            luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
            reply = luna_api_functions.verify(headers, photoId, personId)
            self.assertEqual(len(reply.body["candidates"]), 1, authStr(auth))
            self.assertResultMatching(reply.body["candidates"][0], authStr(auth))
            self.assertTrue(reply.body["candidates"][0]["person_id"] == personId, authStr(auth))
            self.assertTrue(reply.body["candidates"][0]["similarity"] > sim, authStr(auth))

        verify2PhotoTest()

    def test_matching_search_bad_id_query_param(self):
        """
        .. test:: test_matching_search_bad_id_query_param

            :resources: "/matching/search"
            :description: failed matching search with bad type of query params
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def matchingBadIdQueryParamTest(headers, auth):
            testCases = CaseGenerator.badIdQueryParamsTestSuiteVerifyGenerator(
                1, self.photoId, self.personId
            )

            self.matchingBadIdQueryParams(headers, auth, testCases)

        matchingBadIdQueryParamTest()

    def test_matching_verify_non_exist_id(self):
        """
        .. test:: test_matching_verify_non_exist_id

            :resources: "/matching/match"
            :description: trying to verify with non exist id value (uuid4)
            :LIS: No
            :tag: Match
        """
        @self.authorization
        def matchingNonExistIdTest(headers, auth):
            testCases = (
                {
                    "queries": {"descriptor_id": self.photoId, "person_id": self.nonExistsId},
                    "error": Error.PersonNotFound,
                    "msgFormat": None
                },
                {
                    "queries": {"person_id": self.personId, "descriptor_id": self.nonExistsId},
                    "error": Error.DescriptorNotFound,
                    "msgFormat": None
                }
            )
            self.matchingNonExistIdTest(headers, auth, testCases)

        matchingNonExistIdTest()

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
            queryParams = {"person_id": self.personWithoutPhoto, "descriptor_id": self.photoId}
            self.matchEmptyPersonTest(headers, auth, queryParams)

        matchEmptyPersonTest()

    def test_matching_verify_not_consistent_query_params(self):
        """
        .. test:: test_matching_match_not_consistent_query_params

            :resources: "/matching/verify"
            :description: trying to match with no full query params (one of necessary param is missing)
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchingNonConsistentTest(headers, auth):
            testCases = (
                {
                    "queries": {"descriptor_id": self.photoId},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [["person_id"]]
                },
                {
                    "queries": {"person_id": self.personId},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [["descriptor_id"]]
                }
            )
            self.matchingNonConsistentTest(headers, auth, testCases)

        matchingNonConsistentTest()
