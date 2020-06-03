import uuid

from crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase, authStr
from tests.resources import shortPersonList
from tests import luna_api_functions


class TestPhotoLinkList(TestBase):
    """
    Tests link descriptor to list
    """

    def setUp(self):
        self.createAccountAndToken()

    def test_link_link_descriptor_to_list(self):
        """
        .. test:: test_link_link_descriptor_to_list

            :resources: "/storage/descriptors/\{descriptor_id\}/linked_lists"
            :description: success linking descriptor to list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def linkListTest(headers, auth):
            photoId = self.createPhoto(headers)
            listId = self.createList(headers, False)
            replyInfo = luna_api_functions.linkListToDescriptor(headers, photoId, listId, 'attach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))

        linkListTest()

    def test_link_link_descriptor_to_list_with_photo(self):
        """
        .. test:: test_link_link_descriptor_to_list_with_photo

            :resources: "/storage/descriptors/\{descriptor_id\}/linked_lists"
            :description: success linking descriptor to list with other descriptor
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def linkListWithPhotoTest(headers, auth):
            photoId = self.createPhoto(headers)
            listId = self.createList(headers, False)
            replyInfo = luna_api_functions.linkListToDescriptor(headers, photoId, listId, 'attach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            photoId = self.createPhoto(headers)
            replyInfo = luna_api_functions.linkListToDescriptor(headers, photoId, listId, 'attach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))

        linkListWithPhotoTest()

    def test_link_get_linking_lists(self):
        """
        .. test:: test_link_get_linking_lists

            :resources: "/storage/descriptors/\{descriptor_id\}/linked_lists"
            :description: success getting of linking list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def getLinkedLists(headers, auth):
            photoId = self.createPhoto(headers)
            listId = self.createList(headers, False)
            luna_api_functions.linkListToDescriptor(headers, photoId, listId, 'attach')
            photoId1 = self.createPhoto(headers)
            luna_api_functions.linkListToDescriptor(headers, photoId1, listId, 'attach')
            replyInfo = luna_api_functions.getLinkedListsToDescriptor(headers, photoId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertTrue(listId in replyInfo.body["lists"], authStr(auth))
            listId = replyInfo.body["lists"]
            replyInfo = luna_api_functions.getLinkedListsToDescriptor(headers, photoId1)
            self.assertTrue(listId == replyInfo.body["lists"], authStr(auth))

        getLinkedLists()

    def test_link_detach_descriptor_from_list(self):
        """
        .. test:: test_link_detach_descriptor_from_list

            :resources: "/storage/descriptors/\{descriptor_id\}/linked_lists"
            :description: success linking descriptor from list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def detachLink(headers, auth):
            photoId = self.createPhoto(headers)
            listId1 = self.createList(headers, False)
            luna_api_functions.linkListToDescriptor(headers, photoId, listId1, 'attach')
            listId2 = self.createList(headers, False)
            luna_api_functions.linkListToDescriptor(headers, photoId, listId2, 'attach')
            replyInfo = luna_api_functions.getLinkedListsToDescriptor(headers, photoId)
            self.assertTrue(listId1 in replyInfo.body["lists"], authStr(auth))
            self.assertTrue(listId2 in replyInfo.body["lists"], authStr(auth))

            replyInfo = luna_api_functions.linkListToDescriptor(headers, photoId, listId1, 'detach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getLinkedListsToDescriptor(headers, photoId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertTrue(listId2 in replyInfo.body["lists"], authStr(auth))
            self.assertTrue(len(replyInfo.body["lists"]) == 1, authStr(auth))
            replyInfo = luna_api_functions.match(headers, listId=listId1, descriptorId=photoId)
            self.assertEqual(replyInfo.statusCode, 201, authStr(auth))
            self.assertEqual(0, len(replyInfo.body["candidates"]), authStr(auth))

        detachLink()

    def test_link_detach_descriptor_from_non_linking_list(self):
        """
        .. test:: test_link_detach_descriptor_from_non_linking_list

            :resources: "/storage/descriptors/\{descriptor_id\}/linked_lists"
            :description: success detach descriptor from list without linking
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def detachNonLinkedList(headers, auth):
            photoId = self.createPhoto(headers)
            listId = self.createList(headers, False)
            replyInfo = luna_api_functions.linkListToDescriptor(headers, photoId, listId, 'detach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getLinkedListsToDescriptor(headers, photoId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertTrue(len(replyInfo.body["lists"]) == 0, authStr(auth))

        detachNonLinkedList()

    def test_link_link_non_exist_descriptor_to_list(self):
        """
        .. test:: test_link_link_non_exist_descriptor_to_list

            :resources: "/storage/descriptors/\{descriptor_id\}/linked_lists"
            :description: try linking non exist descriptor to list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def linkToNonExistPerson(headers, auth):
            listId = self.createList(headers, False)
            replyInfo = luna_api_functions.linkListToDescriptor(headers, str(uuid.uuid4()), listId, 'attach')
            self.assertErrorRestAnswer(replyInfo, 404, Error.DescriptorNotFound, auth=authStr(auth))
            listId = self.createList(headers, False)
            replyInfo = luna_api_functions.linkListToDescriptor(headers, str(uuid.uuid4()), listId, 'detach')
            self.assertErrorRestAnswer(replyInfo, 404, Error.DescriptorNotFound, auth=authStr(auth))

        linkToNonExistPerson()

    def test_link_link_exist_descriptor_to_non_list(self):
        """
        .. test:: test_link_link_exist_descriptor_to_non_list

            :resources: "/storage/descriptors/\{descriptor_id\}/linked_lists"
            :description: try linking descriptor to non exist list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def linkToNonExistList(headers, auth):
            photoId = self.createPhoto(headers)
            replyInfo = luna_api_functions.linkListToDescriptor(headers, photoId, str(uuid.uuid4()), 'attach')
            self.assertErrorRestAnswer(replyInfo, 400, Error.ListNotFound, auth=authStr(auth))
            replyInfo = luna_api_functions.linkListToDescriptor(headers, photoId, str(uuid.uuid4()), 'detach')
            self.assertErrorRestAnswer(replyInfo, 400, Error.ListNotFound, auth=authStr(auth))

        linkToNonExistList()

    def test_link_link_descriptor_to_list_with_bad_id(self):
        """
        .. test:: test_link_link_descriptor_to_list_with_bad_id

            :resources: "/storage/descriptors/\{descriptor_id\}/linked_lists"
            :description: try linking descriptor to list with non correct id
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def linkToBadFormatList(headers, auth):
            photoId = self.createPhoto(headers)
            replyInfo = luna_api_functions.linkListToDescriptor(headers, photoId, str(uuid.uuid4()) + "1", 'attach')
            self.assertErrorRestAnswer(replyInfo, 400, Error.BadQueryParams, auth=authStr(auth),
                                       msgFormat=["list_id"])
            replyInfo = luna_api_functions.linkListToDescriptor(headers, photoId, str(uuid.uuid4()) + "1", 'detach')
            self.assertErrorRestAnswer(replyInfo, 400, Error.BadQueryParams, auth=authStr(auth),
                                       msgFormat=["list_id"])

        linkToBadFormatList()

    def test_link_link_descriptor_to_list_bad_query_params_do(self):
        """
        .. test:: test_link_link_descriptor_to_list_bad_query_params_do

            :resources: "/storage/descriptors/\{descriptor_id\}/linked_lists"
            :description: try linking descriptor to list with query param "dettach"
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def badDoParameter(headers, auth):
            photoId = self.createPhoto(headers)
            listId = self.createList(headers, False)
            replyInfo = luna_api_functions.linkListToDescriptor(headers, photoId, listId, "dettach")
            self.assertErrorRestAnswer(replyInfo, 400, Error.BadQueryParams, auth=authStr(auth), msgFormat=["do"])

        badDoParameter()

    def test_link_match_with_list_after_detach(self):
        """
        .. test:: test_link_match_with_list_after_detach

            :resources: "/storage/descriptors/\{descriptor_id\}/linked_lists"
            :description: success match  with descriptor's list after detach descriptor from it
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def matchDescriptorsTest(headers, auth):
            listId = self.createList(headers, False)
            photoIdForRemove = ""
            for img in shortPersonList:
                photoId = luna_api_functions.extractDescriptors(headers, filename=img).body["faces"][0]["id"]
                luna_api_functions.linkListToDescriptor(headers, photoId, listId, 'attach')
                photoIdForRemove = photoId

            replyInfo = luna_api_functions.linkListToDescriptor(headers, photoIdForRemove, listId, 'detach')
            self.assertTrue(replyInfo.statusCode == 204, authStr(auth))
            photoId = self.createPhoto(headers)
            reply = luna_api_functions.match(headers, listId=listId, descriptorId=photoId)
            self.assertTrue(reply.statusCode == 201, authStr(auth))
            self.assertSuccessMatching(reply, authStr(auth), False)
            self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))

        matchDescriptorsTest()
