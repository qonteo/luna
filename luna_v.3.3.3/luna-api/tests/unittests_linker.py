from lunavl.luna_api import makeRequest
from crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase, authStr
from tests import luna_api_functions
from tests.luna_api_functions import SERVER_URL
from uuid import uuid4


class TestLinker(TestBase):
    """
    Tests link persons and descriptors to list.
    """

    def setUp(self):
        self.createAccountAndToken()

    def test_linker_attach_persons_to_list(self):
        """
        .. test:: test_linker_attach_persons_to_list

            :resources: "/storage/linker"
            :description: success attaching persons to list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerAttachPersonsToList(headers, auth):
            personIds = self.createPersons(headers, 3)
            listId = self.createList(headers)
            attachReply = luna_api_functions.link(headers, listId, personIds=personIds, action='attach')
            self.assertEqual(attachReply.statusCode, 204, authStr(auth))

            personsRes = [luna_api_functions.getPerson(headers, pId, raiseError=True) for pId in personIds]
            self.assertTrue(all(res.success for res in personsRes), personsRes)
            self.assertTrue(all(res.body['lists'] == [listId] for res in personsRes), personsRes)

        testLinkerAttachPersonsToList()

    def test_linker_detach_persons_from_list(self):
        """
        .. test:: test_linker_detach_persons_from_list

            :resources: "/storage/linker"
            :description: success detaching persons from list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerDetachPersonsFromList(headers, auth):
            personIds = self.createPersons(headers, 3)
            listId = self.createList(headers)
            luna_api_functions.link(headers, listId, personIds=personIds, action='attach', raiseError=True)
            attachReply = luna_api_functions.link(headers, listId, personIds=personIds, action='detach')
            self.assertEqual(attachReply.statusCode, 204, authStr(auth))

            personsRes = [luna_api_functions.getPerson(headers, pId, raiseError=True) for pId in personIds]
            self.assertTrue(all(res.success for res in personsRes), personsRes)
            self.assertTrue(all(res.body['lists'] == [] for res in personsRes), personsRes)

        testLinkerDetachPersonsFromList()

    def test_linker_attach_attached_person_to_list(self):
        """
        .. test:: test_linker_attach_attached_person_to_list

            :resources: "/storage/linker"
            :description: success double-attaching person to list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerAttachAttachedPersonToList(headers, auth):
            personIds = self.createPersons(headers, 3)
            listId = self.createList(headers)
            luna_api_functions.link(headers, listId, personIds=[personIds[0]], action='attach', raiseError=True)
            # double-attach person is ok?!
            attachReply = luna_api_functions.link(headers, listId, personIds=personIds, action='attach')
            self.assertEqual(attachReply.statusCode, 204, authStr(auth))

            personRes = [luna_api_functions.getPerson(headers, pId, raiseError=True) for pId in personIds]
            self.assertTrue(all(res.success for res in personRes), personRes)
            # all persons are attached?!?!
            self.assertTrue(all(res.body['lists'] == [listId] for res in personRes), personRes)

        testLinkerAttachAttachedPersonToList()

    def test_linker_attach_nonexistent_person_to_list(self):
        """
        .. test:: test_linker_attach_nonexistent_person_to_list

            :resources: "/storage/linker"
            :description: fail attach nonexistent person to list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerAttachNonexistentPersonToList(headers, auth):
            personIds = list(self.createPersons(headers, 2)) + [str(uuid4())]
            listId = self.createList(headers)
            attachReply = luna_api_functions.link(headers, listId, personIds=personIds, action='attach')
            self.assertErrorRestAnswer(attachReply, 400, Error.PersonsNotFound, auth=authStr(auth))

            personRes = [luna_api_functions.getPerson(headers, pId, raiseError=True) for pId in personIds[:2]]
            self.assertTrue(all(res.success for res in personRes), personRes)
            self.assertTrue(all(res.body['lists'] == [] for res in personRes), personRes)

        testLinkerAttachNonexistentPersonToList()

    def test_linker_attach_persons_to_nonexistent_list(self):
        """
        .. test:: test_linker_attach_persons_to_nonexistent_list

            :resources: "/storage/linker"
            :description: fail attach persons to nonexistent list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerAttachPersonsToNonexistentList(headers, auth):
            personIds = self.createPersons(headers, 3)
            listId = str(uuid4())
            attachReply = luna_api_functions.link(headers, listId, personIds=personIds, action='attach')
            self.assertErrorRestAnswer(attachReply, 400, Error.ListNotFound, auth=authStr(auth))

            personRes = [luna_api_functions.getPerson(headers, pId, raiseError=True) for pId in personIds]
            self.assertTrue(all(res.success for res in personRes), personRes)
            self.assertTrue(all(res.body['lists'] == [] for res in personRes), personRes)

        testLinkerAttachPersonsToNonexistentList()

    def test_linker_attach_descriptors_to_list(self):
        """
        .. test:: test_linker_attach_descriptors_to_list

            :resources: "/storage/linker"
            :description: success attaching descriptors to list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerAttachDescriptorsToList(headers, auth):
            descriptorIds = [self.createPhoto(headers) for _ in range(3)]
            listId = self.createList(headers, isPersonList=False)
            attachReply = luna_api_functions.link(headers, listId, descriptorIds=descriptorIds, action='attach')
            self.assertEqual(attachReply.statusCode, 204, authStr(auth))

            descriptorsRes = [luna_api_functions.getDescriptor(headers, dId, raiseError=True) for dId in descriptorIds]
            self.assertTrue(all(res.success for res in descriptorsRes), descriptorsRes)
            self.assertTrue(all(res.body['lists'] == [listId] for res in descriptorsRes), descriptorsRes)

        testLinkerAttachDescriptorsToList()

    def test_linker_detach_descriptors_from_list(self):
        """
        .. test:: test_linker_detach_descriptors_from_list

            :resources: "/storage/linker"
            :description: success detaching descriptors from list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerDetachDescriptorsFromList(headers, auth):
            descriptorIds = [self.createPhoto(headers) for _ in range(3)]
            listId = self.createList(headers, isPersonList=False)
            luna_api_functions.link(headers, listId, descriptorIds=descriptorIds, action='attach', raiseError=True)
            attachReply = luna_api_functions.link(headers, listId, descriptorIds=descriptorIds, action='detach')
            self.assertEqual(attachReply.statusCode, 204, authStr(auth))

            descriptorRes = [luna_api_functions.getDescriptor(headers, dId, raiseError=True) for dId in descriptorIds]
            self.assertTrue(all(res.success for res in descriptorRes), descriptorRes)
            self.assertTrue(all(res.body['lists'] == [] for res in descriptorRes), descriptorRes)

        testLinkerDetachDescriptorsFromList()

    def test_linker_attach_attached_descriptor_to_list(self):
        """
        .. test:: test_linker_attach_attached_descriptor_to_list

            :resources: "/storage/linker"
            :description: success double-attaching descriptor to list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerAttachAttachedDescriptorToList(headers, auth):
            descriptorIds = [self.createPhoto(headers) for _ in range(3)]
            listId = self.createList(headers, isPersonList=False)
            luna_api_functions.link(headers, listId, descriptorIds=[descriptorIds[0]], action='attach', raiseError=True)
            # double-attach descriptor is ok?!
            attachReply = luna_api_functions.link(headers, listId, descriptorIds=descriptorIds, action='attach')
            self.assertEqual(attachReply.statusCode, 204, authStr(auth))

            descriptorRes = [luna_api_functions.getDescriptor(headers, dId, raiseError=True) for dId in descriptorIds]
            self.assertTrue(all(res.success for res in descriptorRes), descriptorRes)
            # all descriptors are attached?!?!
            self.assertTrue(all(res.body['lists'] == [listId] for res in descriptorRes), descriptorRes)

        testLinkerAttachAttachedDescriptorToList()

    def test_linker_attach_nonexistent_descriptor_to_list(self):
        """
        .. test:: test_linker_attach_nonexistent_descriptor_to_list

            :resources: "/storage/linker"
            :description: fail attaching nonexistent descriptor to list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerAttachNonexistentDescriptorToList(headers, auth):
            descriptorIds = [self.createPhoto(headers) for _ in range(2)] + [str(uuid4())]
            listId = self.createList(headers, isPersonList=False)
            attachReply = luna_api_functions.link(headers, listId, descriptorIds=descriptorIds, action='attach')
            self.assertErrorRestAnswer(attachReply, 400, Error.FacesNotFound, auth=authStr(auth))

            descriptorRes = [luna_api_functions.getDescriptor(headers, dId, raiseError=True) for dId in descriptorIds[:2]]
            self.assertTrue(all(res.success for res in descriptorRes), descriptorRes)
            self.assertTrue(all(res.body['lists'] == [] for res in descriptorRes), descriptorRes)

        testLinkerAttachNonexistentDescriptorToList()

    def test_linker_attach_descriptors_to_nonexistent_list(self):
        """
        .. test:: test_linker_attach_descriptors_to_nonexistent_list

            :resources: "/storage/linker"
            :description: fail attaching descriptor to nonexistent list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerAttachDescriptorsToNonexistentList(headers, auth):
            descriptorIds = [self.createPhoto(headers) for _ in range(3)]
            listId = str(uuid4())
            attachReply = luna_api_functions.link(headers, listId, descriptorIds=descriptorIds, action='attach')
            self.assertErrorRestAnswer(attachReply, 400, Error.ListNotFound, auth=authStr(auth))

            descriptorRes = [luna_api_functions.getDescriptor(headers, dId, raiseError=True) for dId in descriptorIds]
            self.assertTrue(all(res.success for res in descriptorRes), descriptorRes)
            self.assertTrue(all(res.body['lists'] == [] for res in descriptorRes), descriptorRes)

        testLinkerAttachDescriptorsToNonexistentList()

    def test_linker_not_json(self):
        """
        .. test:: test_linker_not_json

            :resources: "/storage/linker"
            :description: fail processing not-json body
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerNotJson(headers, auth):
            attachReply = makeRequest(SERVER_URL + '/storage/linker', 'PATCH', body='123',
                                      additionalHeaders={"Content-Type": "application/json"}, **headers)
            self.assertErrorRestAnswer(attachReply, 400, Error.RequestNotContainsJson, auth=authStr(auth))

        testLinkerNotJson()

    def test_linker_no_objects(self):
        """
        .. test:: test_linker_no_objects

            :resources: "/storage/linker"
            :description: fail processing body with empty attach candidates
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerNoObjects(headers, auth):
            listId = "ec12ca77-f16e-46b4-8a20-7180be9b0cf6"
            attachReply = luna_api_functions.link(headers, listId, action='attach')
            self.assertEqual(attachReply.statusCode, 400, attachReply)
            self.assertEqual(attachReply.body['error_code'], Error.BadInputJson.errorCode, attachReply)

        testLinkerNoObjects()

    def test_linker_person_to_descriptors_list(self):
        """
        .. test:: test_linker_person_to_descriptors_list

            :resources: "/storage/linker"
            :description: success attaching persons to descriptors list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerPersonToDescriptorsList(headers, auth):
            listDescriptorsId = self.createList(headers, isPersonList=False)
            personIds = self.createPersons(headers, 3)
            # success link persons to descriptors list?!
            attachReply = luna_api_functions.link(headers, listDescriptorsId, personIds=personIds, action='attach')
            self.assertEqual(attachReply.statusCode, 204, authStr(auth))

            personRes = [luna_api_functions.getPerson(headers, pId, raiseError=True) for pId in personIds]
            self.assertTrue(all(res.success for res in personRes), personRes)
            # all persons are attached?!?!
            self.assertTrue(all(res.body['lists'] == [listDescriptorsId] for res in personRes), personRes)

        testLinkerPersonToDescriptorsList()

    def test_linker_descriptors_to_persons_list(self):
        """
        .. test:: test_linker_descriptors_to_persons_list

            :resources: "/storage/linker"
            :description: success attaching descriptors to persons list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def testLinkerDescriptorsToPersonsList(headers, auth):
            listPersonsId = self.createList(headers)
            descriptorIds = [self.createPhoto(headers) for _ in range(3)]
            # success link descriptors to persons list?!
            attachReply = luna_api_functions.link(headers, listPersonsId, descriptorIds=descriptorIds, action='attach')
            self.assertEqual(attachReply.statusCode, 204, authStr(auth))

            descriptorsRes = [luna_api_functions.getDescriptor(headers, dId, raiseError=True) for dId in descriptorIds]
            self.assertTrue(all(res.success for res in descriptorsRes), descriptorsRes)
            # all descriptors are attached?!?!
            self.assertTrue(all(res.body['lists'] == [listPersonsId] for res in descriptorsRes), descriptorsRes)

        testLinkerDescriptorsToPersonsList()
