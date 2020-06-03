import unittest

from tests.classes import authStr
from tests.config import LUNA_IMAGE_STORE_OFF
from tests.functions import createPayloadImg
from tests.matcher.matcher_caseGenerator import CaseGenerator
from tests.matcher.unittests_abstract_match import TestAbstractMatching
from tests.resources import standardImage, severalFaces, warpedImage, base64Files, onePersonList
from crutches_on_wheels.errors.errors import Error
from tests import luna_api_functions


class TestMatchingSearch(TestAbstractMatching):
    """
    Tests of matching search
    """

    resource = '/matching/search'

    def setUp(self):
        super().setUp()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        TestMatchingSearch.uploadImage = createPayloadImg(standardImage)
        TestMatchingSearch.isBinary = True

    def test_matching_search_person_list(self):
        """
        .. test:: test_matching_search_person_list

            :resources: "/matching/search"
            :description: success searching by person list
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            reply = luna_api_functions.search(headers, body=createPayloadImg(standardImage), listId=listId)
            self.assertSuccessMatching(reply, authStr(auth))
            self.assertEqual(len(reply.body["candidates"]), 3, authStr(auth))

        searchTest()

    def test_matching_search_descriptors_list(self):
        """
        .. test:: test_matching_search_descriptors_list

            :resources: "/matching/search"
            :description: success searching by descriptors list
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.descriptorsListId
            reply = luna_api_functions.search(headers, body=createPayloadImg(standardImage), listId=listId)
            self.assertSuccessMatching(reply, authStr(auth), False)
            self.assertEqual(len(reply.body["candidates"]), 3, authStr(auth))

        searchTest()

    def test_matching_search_dynamic_descriptors_list(self):
        """
        .. test:: test_matching_search_dynamic_descriptors_list

            :resources: "/matching/search"
            :description: success searching by dynamic descriptors list
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def searchTest(headers, auth):
            listPhotoId = self.dynamicDescriptorsList
            reply = luna_api_functions.search(headers, body=createPayloadImg(standardImage),
                                              descriptorIds=listPhotoId)
            self.assertSuccessMatching(reply, authStr(auth), False)
            self.assertEqual(len(reply.body["candidates"]), 3, authStr(auth))

        searchTest()

    def test_matching_search_dynamic_persons_list(self):
        """
         .. test:: test_matching_search_dynamic_persons_list

             :resources: "/matching/search"
             :description: success searching by dynamic persons list
             :LIS: No
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listPersonId = self.dynamicPersonsList
            reply = luna_api_functions.search(headers, body=createPayloadImg(standardImage), personIds=listPersonId)
            self.assertSuccessMatching(reply, authStr(auth))
            self.assertEqual(len(reply.body["candidates"]), 3, authStr(auth))

        searchTest()

    def test_matching_search_many_faces(self):
        """
         .. test:: test_matching_search_many_faces

             :resources: "/matching/search"
             :description: trying to search , template is image with several faces
             :LIS: No
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            reply = luna_api_functions.search(headers, body=createPayloadImg(severalFaces), listId=listId)
            self.assertEqual(reply.body["error_code"], Error.ManyFaces.errorCode, authStr(auth))
            self.assertEqual(len(reply.body["detail"]["faces"]), 9, authStr(auth))

        searchTest()

    def test_matching_search_with_exif(self):
        """
         .. test:: test_matching_search_with_exif

             :resources: "/matching/search"
             :description: success searching by persons list with set extract_exif to 0 and 1
             :LIS: No
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            for extract in (True, False):
                reply = luna_api_functions.search(headers, body=createPayloadImg(onePersonList[0]), listId=listId,
                                                  extractExif=extract)
                self.assertSuccessMatching(reply, authStr(auth))
                self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))
                if not extract:
                    self.assertTrue("exif" not in reply.body, authStr(auth))
                else:
                    self.assertTrue("exif" in reply.body, authStr(auth))

        searchTest()

    @unittest.skipIf(LUNA_IMAGE_STORE_OFF, "S3 in LUNA API OFF")
    def test_matching_search_warped_image(self):
        """
         .. test:: test_matching_search_warped_image

             :resources: "/matching/search"
             :description: success searching by persons list with set warped_image to 0 and 1
             :LIS: Yes
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            for warped in ["0", "1"]:
                reply = luna_api_functions.search(headers, body=createPayloadImg(warpedImage), listId=listId,
                                                  warpedImage=warped)
                self.assertSuccessMatching(reply, authStr(auth))
                self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))
                descriptorId = reply.body["face"]["id"]
                if warped == "1":
                    reply = luna_api_functions.getPortrait(headers, descriptorId)
                    body = reply.body
                    with open(warpedImage, "rb") as f:
                        imgBytes = f.read()
                    self.assertEqual(imgBytes, body, authStr(auth))
                else:
                    reply = luna_api_functions.getPortrait(headers, descriptorId)
                    body = reply.body
                    with open(warpedImage, "rb") as f:
                        imgBytes = f.read()
                    self.assertTrue(imgBytes != body, authStr(auth))

        searchTest()

    def test_matching_search_extract_descriptor(self):
        """
         .. test:: test_matching_search_extract_descriptor

             :resources: "/matching/search"
             :description: trying to search by persons list with set extract_descriptor to 0 and 1
             :LIS: No
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            for extract in ["0", "1"]:
                headers['Content-Type'] = 'image/jpeg'
                reply = luna_api_functions.manualRequest('/matching/search', 'POST', body=createPayloadImg(warpedImage),
                                                         isBinary=True, headers=headers,
                                                         queryParams={'list_id': listId, 'extract_descriptor': extract})
                if extract == "0":
                    self.assertErrorRestAnswer(reply, 400, Error.UnsupportedQueryParm,
                                               msgFormat=["extract_descriptor"], auth=authStr(auth))
                else:
                    self.assertSuccessMatching(reply, authStr(auth))
                    self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))

        searchTest()

    def test_matching_search_estimate_attributes(self):
        """
         .. test:: test_matching_search_estimate_attributes

             :resources: "/matching/search"
             :description: success searching by persons list with set estimate_attributes to 0 and 1
             :LIS: No
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            for estimate in ["0", "1"]:
                reply = luna_api_functions.search(headers, body=createPayloadImg(onePersonList[0]), listId=listId,
                                                  estimateAttributes=estimate)
                self.assertSuccessMatching(reply, authStr(auth))
                self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))
                if estimate == "0":
                    self.assertTrue("attributes" not in reply.body["face"], authStr(auth))
                else:
                    self.assertTrue("attributes" in reply.body["face"], authStr(auth))

        searchTest()

    def test_matching_search_estimate_emotions(self):
        """
         .. test:: test_matching_search_estimate_emotions

             :resources: "/matching/search"
             :description: success searching by persons list with set estimate_emotions to 0 and 1
             :LIS: No
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            for estimate in (True, False):
                reply = luna_api_functions.search(headers, body=createPayloadImg(onePersonList[0]), listId=listId,
                                                  estimateEmotions=estimate)
                self.assertSuccessMatching(reply, authStr(auth))
                self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))
                if not estimate:
                    self.assertTrue("attributes" not in reply.body["face"], authStr(auth))
                else:
                    self.assertTrue("attributes" in reply.body["face"], authStr(auth))
                    self.assertTrue("emotions" in reply.body["face"]["attributes"], authStr(auth))

        searchTest()

    def test_matching_search_estimate_head_pose(self):
        """
         .. test:: test_matching_search_estimate_head_pose

             :resources: "/matching/search"
             :description: success searching by person's list with and without estimate head position
             :LIS: No
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            for estimate in (True, False):
                reply = luna_api_functions.search(headers, body=createPayloadImg(onePersonList[0]), listId=listId,
                                                  estimateHeadPose=estimate)
                self.assertSuccessMatching(reply, authStr(auth))
                self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))
                if not estimate:
                    self.assertTrue("attributes" not in reply.body["face"], authStr(auth))
                else:
                    self.assertTrue("attributes" in reply.body["face"], authStr(auth))
                    self.assertTrue("head_pose" in reply.body["face"]["attributes"], authStr(auth))

        searchTest()

    def test_matching_search_estimate_ethnicities(self):
        """
         .. test:: test_matching_search_estimate_ethnicities

             :resources: "/matching/search"
             :description: success searching by persons list with set estimate_ethnicities to 0 and 1
             :LIS: No
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            for estimate in (True, False):
                reply = luna_api_functions.search(headers, body=createPayloadImg(onePersonList[0]), listId=listId,
                                                  estimateEthnicities=estimate)
                self.assertSuccessMatching(reply, authStr(auth))
                self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))
                if not estimate:
                    self.assertTrue("attributes" not in reply.body["face"], authStr(auth))
                else:
                    self.assertTrue("attributes" in reply.body["face"], authStr(auth))
                    self.assertTrue("ethnicities" in reply.body["face"]["attributes"], authStr(auth))

        searchTest()

    def test_matching_search_estimate_quality(self):
        """
         .. test:: test_matching_search_estimate_quality

             :resources: "/matching/search"
             :description: success searching by persons list with set estimate_quality to 0 and 1
             :LIS: No
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            for estimate in ["0", "1"]:
                reply = luna_api_functions.search(headers, body=createPayloadImg(onePersonList[0]), listId=listId,
                                                  estimateQuality=estimate)
                self.assertSuccessMatching(reply, authStr(auth))
                self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))
                if estimate == "0":
                    self.assertTrue("quality" not in reply.body["face"], authStr(auth))
                else:
                    self.assertTrue("quality" in reply.body["face"], authStr(auth))

        searchTest()

    def test_matching_search_quality_threshold(self):
        """
         .. test:: test_matching_search_quality_threshold

             :resources: "/matching/search"
             :description: trying to search by persons list with set quality_threshold to 0 and 0.99
             :LIS: No
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            for threshold in ["0", "0.9999"]:
                reply = luna_api_functions.search(headers, body=createPayloadImg(onePersonList[0]), listId=listId,
                                                  scoreThreshold=threshold)
                if threshold == "0":
                    self.assertSuccessMatching(reply, authStr(auth))
                    self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))
                    self.assertTrue("score" in reply.body["face"], authStr(auth))
                else:
                    self.assertEqual(reply.statusCode, 400)
                    self.assertEqual(reply.body["error_code"],
                                     Error.LowThreshold.errorCode, auth)

        searchTest()

    def test_matching_search_angle_threshold(self):
        """
         .. test:: test_matching_search_angle_threshold

             :resources: "/matching/search"
             :description: trying to search by persons list with set angle threshold to 0 and 180
             :LIS: No
             :tag: Match
         """

        @self.authorization
        def searchTest(headers, auth):
            listId = self.personsListId
            for threshold in [0, 180]:
                for angle in ("pitchLt", "yawLt", "rollLt"):
                    with self.subTest(angle=angle):
                        reply = luna_api_functions.search(headers, body=createPayloadImg(onePersonList[0]),
                                                          listId=listId,
                                                          **{angle: threshold})
                        if threshold == 180:
                            self.assertSuccessMatching(reply, authStr(auth))
                            self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))
                            self.assertTrue("score" in reply.body["face"], authStr(auth))
                        else:
                            self.assertEqual(reply.statusCode, 400)
                            self.assertEqual(reply.body["error_code"],
                                             Error.LowThreshold.errorCode, auth)

        searchTest()

    def test_matching_search_base64_in_list(self):
        """
        .. test:: test_matching_search_base64_in_list

             :resources: "/matching/search"
             :description: success search descriptors from data in base64 encoding
             :LIS: No
             :tag: Match
        """

        @self.authorization
        def searchBase64(headers, auth):
            for base64File in base64Files:
                with self.subTest(contentType=base64File["Content-Type"]):
                    if not base64File["Content-Type"].startswith('image'):
                        continue
                    listId = self.descriptorsListId
                    replyInfo = luna_api_functions.search(headers, body=createPayloadImg(base64File["filename"]),
                                                          listId=listId, contentType=base64File["Content-Type"])
                    self.assertSuccessMatching(replyInfo, authStr(auth), False)

        searchBase64()

    def test_matching_search_base64_with_wrong_type_header(self):
        """
        .. test:: test_matching_search_base64_with_wrong_type_header

             :resources: "/matching/search"
             :description: trying search descriptors from data in base64 encoding and content-type  "image/bmp"
             :LIS: No
             :tag: Match
        """

        @self.authorization
        def searchBase64WithWrongContentTypeHeader(headers, auth):
            listId = self.descriptorsListId
            replyInfo = luna_api_functions.search(headers, body=createPayloadImg(base64Files[0]["filename"]),
                                                  listId=listId, contentType="image/bmp")
            self.assertErrorRestAnswer(replyInfo, 400, Error.ConvertImageToJPGError, auth=authStr(auth))

        searchBase64WithWrongContentTypeHeader()

    def test_matching_search_bad_base64(self):
        """
        .. test:: test_matching_search_bad_base64

             :resources: "/matching/search"
             :description: trying search descriptors from data in non base64
             :LIS: No
             :tag: Match
        """

        @self.authorization
        def searchSendBase64(headers, auth):
            listId = self.descriptorsListId
            headers["Content-Type"] = "image/x-jpeg-base64"
            replyInfo = luna_api_functions.search(headers, body=b'123', listId=listId,
                                                  contentType="image/x-jpeg-base64")
            self.assertErrorRestAnswer(replyInfo, 500, Error.ConvertBase64Error, auth=authStr(auth))

        searchSendBase64()

    def test_matching_search_limit_params(self):
        """
        .. test:: test_matching_search_limit_params

            :resources: "/matching/search"
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
            headers['Content-Type'] = 'image/jpeg'
            self.limitParamsTest(headers, auth, queryParams)

        limitParamsTest()

    def test_matching_search_with_invalid_limit_params(self):
        """
        .. test:: test_matching_search_with_invalid_limit_params

            :resources: "/matching/search"
            :description: testing of invalid values of 'limit' param
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def limitParamsTest(headers, auth):
            queryParams = {"person_id": self.personId, "list_id": self.descriptorsListId}
            self.invalidLimitParamsTest(headers, auth, queryParams)

        limitParamsTest()

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
            testCases = CaseGenerator.badIdQueryParamsTestSuiteSearchGenerator(
                1)
            headers["Content-Type"] = "image/jpeg"
            self.matchingBadIdQueryParams(headers, auth, testCases)

        matchingBadIdQueryParamTest()

    def test_matching_search_non_exist_id(self):
        """
        .. test:: test_matching_search_non_exist_id

            :resources: "/matching/search"
            :description: trying to match with non exist id value (uuid4)
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchingNonExistIdTest(headers, auth):
            testCases = (
                {
                    "queries": {},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [["list_id", "person_ids", "descriptor_ids"]]
                },
            )
            headers["Content-Type"] = "image/jpeg"
            self.matchingNonExistIdTest(headers, auth, testCases)

        matchingNonExistIdTest()

    def test_matching_search_excess_query_params(self):
        """
        .. test:: test_matching_search_excess_query_params

            :resources: "/matching/match"
            :description: success match with too much query params (1 of query param is excess)
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchingExcessTest(headers, auth):
            testCases = (
                {"person_ids": self.dynamicPersonsList,
                 "descriptor_ids": self.dynamicDescriptorsList,
                 "list_id": self.descriptorsListId},
            )
            headers["Content-Type"] = "image/jpeg"
            self.matchingExcessTest(headers, auth, testCases, False)

        matchingExcessTest()

    def test_matching_search_not_consistent_query_params(self):
        """
        .. test:: test_matching_match_not_consistent_query_params

            :resources: "/matching/search"
            :description: trying to match with no full query params (one of necessary param is missing)
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchingNonConsistentTest(headers, auth):
            testCases = (
                {
                    "queries": {},
                    "error": Error.RequiredQueryParameterNotFound,
                    "msgFormat": [["list_id", "person_ids", "descriptor_ids"]]
                },
            )
            headers["Content-Type"] = "image/jpeg"
            self.matchingNonConsistentTest(headers, auth, testCases)

        matchingNonConsistentTest()

    def test_matching_search_empty_list(self):
        """
        .. test:: test_matching_search_empty_list

            :resources: "/matching/search"
            :description: success matching with list which has no id
            :LIS: No
            :tag: Match
        """

        @self.authorization
        def matchEmptyListTest(headers, auth):
            emptyDescriptorListId =  luna_api_functions.createList(headers, listType=False,
                                                                  listData="visionlabs search tests, descriptor").body["list_id"]
            emptyPersonListId = luna_api_functions.createList(headers, listType=True,
                                                                  listData="visionlabs search tests, persons list").body["list_id"]
            testCases = (
                {
                    "query": {"list_id": emptyPersonListId},
                    "isPersons": True
                },
                {
                    "query": {"list_id": emptyDescriptorListId},
                    "isPersons": False
                }
            )
            headers["Content-Type"] = "image/jpeg"
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
            badPersonIds = (self.dynamicPersonsList[0], self.nonExistsId)
            testCases = (
                {
                    "queries": {"descriptor_id": self.photoId, "descriptor_ids": badDescriptorIds},
                    "error": Error.ObjectNotFound,
                    "msgFormat": ["descriptors"]
                },
                {
                    "queries": {"descriptor_id": self.photoId, "person_ids": badPersonIds},
                    "error": Error.ObjectNotFound,
                    "msgFormat": ["person"]
                }

            )
            headers["Content-Type"] = "image/jpeg"
            self.matchNonExistItemListTest(headers, auth, testCases)

        matchNonExistItemListTest()
