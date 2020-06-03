import uuid

from crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase, authStr
from tests.resources import onePersonList
from tests import luna_api_functions


class TestLinkList(TestBase):
    """
    Tests link person to list
    """
    def attachTwoDescToList(self, headers):
        listId1 = luna_api_functions.createList(headers, False).body["list_id"]
        listId2 = luna_api_functions.createList(headers, False).body["list_id"]
        descId = TestBase.createPhoto(headers)
        luna_api_functions.linkListToDescriptor(headers, descId, listId1, "attach")
        luna_api_functions.linkListToDescriptor(headers, descId, listId1, "attach")
        params = {"listId1": listId1, "listId2": listId2, "descId": descId}
        return params

    def setUp(self):
        self.createAccountAndToken()

    def test_link_attach_person_to_list(self):
        """
        .. test:: test_link_attach_person_to_list

            :resources: "/storage/persons/\{person_id\}/linked_lists"
            :description: success attaching person to list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def linkListTest(headers, auth):
            personId = self.createPerson(headers)
            listId = self.createList(headers)
            replyInfo = luna_api_functions.linkListToPerson(headers, personId, listId, 'attach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))

        linkListTest()

    def test_link_attach_person_with_descriptor_to_list(self):
        """
        .. test:: test_link_attach_person_with_descriptor_to_list

            :resources: "/storage/persons/\{person_id\}/linked_lists"
            :description: success attaching person with descriptor to list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def linkListWithPhotoTest(headers, auth):
            personId = self.createPersonWithPhoto(headers)
            listId = self.createList(headers)
            replyInfo = luna_api_functions.linkListToPerson(headers, personId, listId, 'attach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))

        linkListWithPhotoTest()

    def test_link_get_linked_list_to_person(self):
        """
        .. test:: test_link_get_linked_list_to_person

            :resources: "/storage/persons/\{person_id\}/linked_lists"
            :description: success getting lists of person
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def getLinkedLists(headers, auth):
            personId = self.createPersonWithPhoto(headers)
            listId = self.createList(headers)
            luna_api_functions.linkListToPerson(headers, personId, listId, 'attach')
            replyInfo = luna_api_functions.getLinkedListsToPerson(headers, personId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertTrue(listId in replyInfo.body["lists"], authStr(auth))

        getLinkedLists()

    def test_link_detach_person_from_list(self):
        """
        .. test:: test_link_detach_person_from_list

            :resources: "/storage/persons/\{person_id\}/linked_lists"
            :description: success detaching person to list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def detachLink(headers, auth):
            personId = self.createPersonWithPhoto(headers)
            listId1 = self.createList(headers)
            luna_api_functions.linkListToPerson(headers, personId, listId1, 'attach')
            listId2 = self.createList(headers, True)
            luna_api_functions.linkListToPerson(headers, personId, listId2, 'attach')
            replyInfo = luna_api_functions.getLinkedListsToPerson(headers, personId)
            self.assertTrue(listId1 in replyInfo.body["lists"], authStr(auth))
            self.assertTrue(listId2 in replyInfo.body["lists"], authStr(auth))

            replyInfo = luna_api_functions.linkListToPerson(headers, personId, listId1, 'detach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getLinkedListsToPerson(headers, personId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertTrue(listId2 in replyInfo.body["lists"], authStr(auth))
            self.assertTrue(len(replyInfo.body["lists"]) == 1, authStr(auth))
            replyInfo = luna_api_functions.identify(headers, listId=listId1, personId=personId)
            self.assertEqual(replyInfo.statusCode, 201, authStr(auth))
            self.assertEqual(0, len(replyInfo.body["candidates"]), authStr(auth))

        detachLink()

    def test_link_detach_person_with_descriptor_from_list(self):
        """
        .. test:: test_link_detach_person_with_descriptor_from_list

            :resources: "/storage/persons/\{person_id\}/linked_lists"
            :description: success detaching person with descriptor to list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def detachLinkWithoutPhoto(headers, auth):
            personId = self.createPerson(headers)
            listId = self.createList(headers, True)
            luna_api_functions.linkListToPerson(headers, personId, listId, 'attach')
            replyInfo = luna_api_functions.linkListToPerson(headers, personId, listId, 'detach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getLinkedListsToPerson(headers, personId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertTrue(len(replyInfo.body["lists"]) == 0, authStr(auth))

        detachLinkWithoutPhoto()

    def test_link_detach_person_from_non_attaching_list(self):
        """
        .. test:: test_link_detach_person_from_non_attaching_list

            :resources: "/storage/persons/\{person_id\}/linked_lists"
            :description: success detaching person from non attaching list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def detachNonLinkedList(headers, auth):
            personId = self.createPersonWithPhoto(headers)
            listId = self.createList(headers, True)
            replyInfo = luna_api_functions.linkListToPerson(headers, personId, listId, 'detach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getLinkedListsToPerson(headers, personId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertTrue(len(replyInfo.body["lists"]) == 0, authStr(auth))

        detachNonLinkedList()

    def test_link_attach_non_exist_person_to_list(self):
        """
        .. test:: test_link_attach_non_exist_person_to_list

            :resources: "/storage/persons/\{person_id\}/linked_lists"
            :description: try attaching non exist person to list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def linkToNonExistPerson(headers, auth):
            listId = self.createList(headers, True)
            replyInfo = luna_api_functions.linkListToPerson(headers, str(uuid.uuid4()), listId, 'attach')
            self.assertErrorRestAnswer(replyInfo, 404, Error.PersonNotFound, auth = authStr(auth))
            listId = self.createList(headers, True)
            replyInfo = luna_api_functions.linkListToPerson(headers, str(uuid.uuid4()), listId, 'detach')
            self.assertErrorRestAnswer(replyInfo, 404, Error.PersonNotFound, auth = authStr(auth))

        linkToNonExistPerson()

    def test_link_attach_person_to_non_exist_list(self):
        """
        .. test:: test_link_attach_person_to_non_exist_list

            :resources: "/storage/persons/\{person_id\}/linked_lists"
            :description: try attaching person to non exist list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def linkToNonExistList(headers, auth):
            personId = self.createPersonWithPhoto(headers)
            replyInfo = luna_api_functions.linkListToPerson(headers, personId, str(uuid.uuid4()), 'attach')
            self.assertErrorRestAnswer(replyInfo, 400, Error.ListNotFound, auth = authStr(auth))
            replyInfo = luna_api_functions.linkListToPerson(headers, personId, str(uuid.uuid4()), 'detach')
            self.assertErrorRestAnswer(replyInfo, 400, Error.ListNotFound, auth = authStr(auth))

        linkToNonExistList()

    def test_link_link_person_to_list_with_bad_id(self):
        """
        .. test:: test_link_link_person_to_list_with_bad_id

            :resources: "/storage/persons/\{person_id\}/linked_lists"
            :description: try linking person to list with non correct id
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def linkToBadFormatList(headers, auth):
            personId = self.createPersonWithPhoto(headers)
            replyInfo = luna_api_functions.linkListToPerson(headers, personId, str(uuid.uuid4()) + "1", 'attach')
            self.assertErrorRestAnswer(replyInfo, 400, Error.BadQueryParams, auth = authStr(auth), msgFormat = ['list_id'])
            replyInfo = luna_api_functions.linkListToPerson(headers, personId, str(uuid.uuid4()) + "1", 'detach')
            self.assertErrorRestAnswer(replyInfo, 400, Error.BadQueryParams, auth = authStr(auth), msgFormat = ['list_id'])

        linkToBadFormatList()

    def test_link_attach_person_to_list_bad_format_do(self):
        """
        .. test:: test_link_attach_person_to_list_bad_format_do

            :resources: "/storage/persons/\{person_id\}/linked_lists"
            :description: tying attach  person to list with bad format parameter "do"
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def badDoParameter(headers, auth):
            personId = self.createPerson(headers)
            listId = self.createList(headers, True)
            replyInfo = luna_api_functions.linkListToPerson(headers, personId, listId, "dettach")
            self.assertErrorRestAnswer(replyInfo, 400, Error.BadQueryParams, auth = authStr(auth), msgFormat = ["do"])

        badDoParameter()

    def test_link_get_person_in_list(self):
        """
        .. test:: test_link_get_person_in_list

            :resources: "/storage/lists/\{list_id\}"
            :description: success getting persons from  list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def getListPersonsInListTest(headers, auth):
            personIds = []
            listId = self.createList(headers)
            for i in range(10):
                personId = self.createPerson(headers)
                luna_api_functions.linkListToPerson(headers, personId, listId, 'attach')
                personIds.append(personId)

            replyInfo = luna_api_functions.getList(headers, listId, 1, 3)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertTrue("persons" in replyInfo.body, authStr(auth))
            self.assertTrue(len(replyInfo.body["persons"]) == 3, authStr(auth))
            replyInfo = luna_api_functions.getList(headers, listId, 1, 10)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))

            self.assertTrue(len(replyInfo.body["persons"]) == 10, authStr(auth))

            replyIds = [pers["id"] for pers in replyInfo.body["persons"]]

            self.assertTrue(len(set(personIds) - set(replyIds)) == 0, authStr(auth))
            replyInfo = luna_api_functions.getList(headers, listId, 2, 6)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))

            self.assertTrue(len(replyInfo.body["persons"]) == 4, authStr(auth))

        getListPersonsInListTest()

    def test_link_get_descriptors_in_list(self):
        """
        .. test:: test_link_get_descriptors_in_list

            :resources: "/storage/lists/\{list_id\}"
            :description: success getting descriptors from list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def getListPhotosInListTest(headers, auth):
            photoIds = []
            listId = self.createList(headers, False)
            for img in onePersonList:
                photoId = luna_api_functions.extractDescriptors(headers, filename=img).body["faces"][0]["id"]
                luna_api_functions.linkListToDescriptor(headers, photoId, listId, 'attach')
                photoIds.append(photoId)

            replyInfo = luna_api_functions.getList(headers, listId, 1, 3)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertTrue("descriptors" in replyInfo.body, authStr(auth))
            self.assertTrue(len(replyInfo.body["descriptors"]) == 3, authStr(auth))
            replyInfo = luna_api_functions.getList(headers, listId, 1, 10)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))

            replyIds = [pers["id"] for pers in replyInfo.body["descriptors"]]

            self.assertTrue(len(replyInfo.body["descriptors"]) == 6, authStr(auth))
            self.assertTrue(len(set(photoIds) - set(replyIds)) == 0, authStr(auth))
            replyInfo = luna_api_functions.getList(headers, listId, 2, 2)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))

            self.assertTrue(len(replyInfo.body["descriptors"]) == 2, authStr(auth))

        getListPhotosInListTest()

    def test_link_get_descriptor_from_different_list(self):
        """
        .. test:: test_link_get_descriptor_from_different_list

            :resources: "/storage/lists/{list_id} (descriptors_example)"
            :description: success getting descriptor from two different list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def add_descriptors(headers, auth):
            param = self.attachTwoDescToList(headers)
            getList1 = luna_api_functions.getList(headers, param['listId1'], '1', '30').body
            getList2 = luna_api_functions.getList(headers, param['listId1'], '1', '30').body
            self.assertTrue("descriptors" in getList1, authStr(auth))
            self.assertTrue("descriptors" in getList2, authStr(auth))
            descInList1 = getList1["descriptors"][0]["id"]
            descInList2 = getList2["descriptors"][0]["id"]
            self.assertEqual(param['descId'], descInList1, authStr(auth))
            self.assertEqual(param['descId'], descInList2, authStr(auth))

        add_descriptors()

    def test_link_detach_descriptor_from_different_list(self):
        """
        .. test:: test_link_detach_descriptor_from_different_list

            :resources: "/storage/lists/{list_id}   (descriptors_example)"
            :description: success getting delete descriptors in different list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def delete_descriptors(headers, auth):
            param = self.attachTwoDescToList(headers)
            list1 = luna_api_functions.getList(headers, param["listId1"], '1', '30').body
            luna_api_functions.linkListToDescriptor(headers, param["descId"], param["listId2"], "detach")
            detached_list = luna_api_functions.getList(headers, param["listId2"], '1', '30').body
            descId = list1["descriptors"][0]["id"]
            self.assertEqual(param["descId"], descId, authStr(auth))
            self.assertTrue(detached_list["descriptors"] == [], authStr(auth))

        delete_descriptors()

    def test_link_descriptors_get_descriptors_in_list(self):
        """
        .. test:: test_linked_descriptors_get_descriptors_in_list

            :resources: "/storage/lists/{list_id}"
            :description: success getting descriptors from list
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def check_descriptor_in_person(headers, auth):
            photoId = TestBase.createPhoto(headers)
            personId = luna_api_functions.createPerson(headers).body['person_id']
            luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
            listId = luna_api_functions.createList(headers, True).body['list_id']
            luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
            luna_api_functions.linkListToPerson(headers, personId, listId, "attach")
            personList = luna_api_functions.getList(headers, listId, '1', '10').body["persons"]
            self.assertEqual(personId, personList[0]['id'], authStr(auth))
            self.assertEqual(photoId, personList[0]["descriptors"][0], authStr(auth))

        check_descriptor_in_person()

    def test_link_pagination_in_list(self):
        """
        .. test:: test_test_pagination_in_list

            :resources: "/storage/lists/{list_id}"
            :description: pagination test, 1 page should not be identical to 2 pages
            :LIS: No
            :tag: Linking
        """
        @self.authorization
        def pagination_test(headers, auth):
            listId = luna_api_functions.createList(headers, False).body["list_id"]
            for i in range(0, 11):
                descId = TestBase.createPhoto(headers)
                luna_api_functions.linkListToDescriptor(headers, descId, listId, 'attach')
            page1 = luna_api_functions.getList(headers, listId, '1', '10').body
            descIds = []
            for i in range(0, len(page1['descriptors'])):
                descIds.append(page1['descriptors'][i]['id'])
            page2 = luna_api_functions.getList(headers, listId, '2', '10').body
            self.assertTrue(len(page2['descriptors']) == 1, authStr(auth))
            self.assertNotIn(page2['descriptors'][0]['id'], descIds, authStr(auth))

        pagination_test()
