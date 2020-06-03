import uuid

from crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase, authStr
from tests import luna_api_functions


class TestLinkDescriptor(TestBase):
    """
    Tests link descriptor to person
    """

    def setUp(self):
        self.createAccountAndToken()

    def createPersonAndDescriptor(self, headers):
        """
        Create person person and descriptor

        :param headers: header for creating

        :return: personId, photoId
        """
        personId = self.createPerson(headers)
        photoId = self.createPhoto(headers)
        return personId, photoId

    def createPersonWithListAndDescriptor(self, headers):
        """
        Create person person with list and descriptor

        :param headers: header for creating

        :return: personId, photoId
        """
        personId = self.createPersonWithList(headers)
        photoId = self.createPhoto(headers)
        return personId, photoId

    def test_link_attach_descriptor_to_person(self):
        """
        .. test:: test_link_attach_descriptor_to_person

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: success attaching descriptor to person
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def linkDescriptorTest(headers, auth):
            personId, photoId = self.createPersonAndDescriptor(headers)
            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))

        linkDescriptorTest()

    def test_link_attach_descriptor_with_person_to_other_person(self):
        """
        .. test:: test_link_attach_descriptor_to_person

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: try to attach descriptor with person to other person
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def linkDescriptorTest(headers, auth):
            personId, photoId = self.createPersonAndDescriptor(headers)
            luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")

            personId2 = self.createPerson(headers)
            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId2, photoId, "attach")
            self.assertErrorRestAnswer(replyInfo, 409, Error.LinkDescriptorAlreadyExist, auth = authStr(auth))

        linkDescriptorTest()

    def test_link_attach_descriptor_to_person_with_list(self):
        """
        .. test:: test_link_link_descriptor_to_person_with_list

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: success attaching descriptor to person which in list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def linkDescriptorTest(headers, auth):
            personId, photoId = self.createPersonWithListAndDescriptor(headers)

            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))

        linkDescriptorTest()

    def test_link_get_linking_descriptors_to_person(self):
        """
        .. test:: test_link_get_linking_descriptors_to_person

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: success getting descriptors of person
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def getLinkedDescriptorTest(headers, auth):
            personId, photoId = self.createPersonWithListAndDescriptor(headers)

            luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
            replyInfo = luna_api_functions.getLinkedDescriptorToPerson(headers, personId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertEqual(replyInfo.body["descriptors"][0], photoId, authStr(auth))

        getLinkedDescriptorTest()

    def test_link_duplicate_link_descriptor_to_person(self):
        """
        .. test:: test_link_duplicate_link_descriptor_to_person

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: trying linking descriptor already attach to person
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def duplicateLinkedDescriptorTest(headers, auth):
            personId, photoId = self.createPersonWithListAndDescriptor(headers)

            luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
            self.assertErrorRestAnswer(replyInfo, 409, Error.LinkDescriptorAlreadyExist, authStr(auth))

        duplicateLinkedDescriptorTest()

    def test_link_detach_descriptor_from_person(self):
        """
        .. test:: test_link_detach_descriptor_from_person

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: success detaching descriptor from person in list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def detachPerson(headers, auth):
            personId, photoId = self.createPersonWithListAndDescriptor(headers)
            luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
            replyInfo = luna_api_functions.getLinkedDescriptorToPerson(headers, personId)
            self.assertTrue((photoId in replyInfo.body["descriptors"]), authStr(auth))

            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "detach")
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getLinkedDescriptorToPerson(headers, personId)
            self.assertTrue(not (photoId in replyInfo.body["descriptors"]), authStr(auth))

        detachPerson()

    def test_link_detach_descriptor_from_person_without_list(self):
        """
        .. test:: test_link_detach_descriptor_from_person

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: success detaching descriptor from person in not list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def detachPerson(headers, auth):
            personId, photoId = self.createPersonAndDescriptor(headers)
            luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
            replyInfo = luna_api_functions.getLinkedDescriptorToPerson(headers, personId)
            self.assertTrue((photoId in replyInfo.body["descriptors"]), authStr(auth))

            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "detach")
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getLinkedDescriptorToPerson(headers, personId)
            self.assertTrue(not (photoId in replyInfo.body["descriptors"]), authStr(auth))

        detachPerson()

    def test_link_attach_two_descriptors_to_person(self):
        """
        .. test:: test_link_attach_two_descriptors_to_person

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: success attaching two descriptor to person
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def attachTwoDescriptorsToPerson(headers, auth):
            personId, photoId1 = self.createPersonWithListAndDescriptor(headers)
            photoId2 = self.createPhoto(headers)
            luna_api_functions.linkDescriptorToPerson(headers, personId, photoId1, "attach")
            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, photoId2, "attach")

            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getLinkedDescriptorToPerson(headers, personId)
            self.assertEqual(len(replyInfo.body["descriptors"]), 2, authStr(auth))
            self.assertTrue(photoId1 in replyInfo.body["descriptors"], authStr(auth))
            self.assertTrue(photoId2 in replyInfo.body["descriptors"], authStr(auth))
            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, photoId1, "detach")

            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))

            replyInfo = luna_api_functions.getLinkedDescriptorToPerson(headers, personId)
            self.assertEqual(len(replyInfo.body["descriptors"]), 1)
            self.assertTrue(photoId2 in replyInfo.body["descriptors"])

        attachTwoDescriptorsToPerson()

    def test_link_attach_non_exist_descriptor_to_person(self):
        """
        .. test:: test_link_attach_two_descriptors_to_person

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: tying attach non exist descriptor to person
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def attachToNonExistPhoto(headers, auth):
            personId = self.createPerson(headers)
            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, str(uuid.uuid4()), "attach")
            self.assertErrorRestAnswer(replyInfo, 400, Error.DescriptorNotFound, auth = authStr(auth))
            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, str(uuid.uuid4()), "detach")
            self.assertErrorRestAnswer(replyInfo, 400, Error.DescriptorNotFound, auth = authStr(auth))

        attachToNonExistPhoto()

    def test_link_attach_descriptor_to_non_exist_person(self):
        """
        .. test:: test_link_attach_descriptor_to_non_exist_person

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: tying attach  descriptor to non exist person
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def attachToNonExistPerson(headers, auth):
            photoId = self.createPhoto(headers)
            for action in ["attach", "detach"]:
                replyInfo = luna_api_functions.linkDescriptorToPerson(headers, str(uuid.uuid4()), photoId, action)
                self.assertErrorRestAnswer(replyInfo, 404, Error.PersonNotFound, auth = authStr(auth))

        attachToNonExistPerson()

    def test_link_attach_bad_format_descriptor_to_person(self):
        """
        .. test:: test_link_attach_bad_format_descriptor_to_person

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: tying attach  descriptor to person with bad format uuid in parameter "descriptor_id"
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def badTypeDescriptorParameter(headers, auth):
            personId = self.createPerson(headers)
            for action in ["attach", "detach"]:
                replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, str(uuid.uuid4()) + "1",
                                                                      action)
                self.assertErrorRestAnswer(replyInfo, 400, Error.BadQueryParams, auth = authStr(auth),
                                           msgFormat = ["descriptor_id"])

        badTypeDescriptorParameter()

    def test_link_attach_descriptor_to_person_bad_format_do(self):
        """
        .. test:: test_link_attach_descriptor_to_person_bad_format_do

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: tying attach  descriptor to  person with bad format parameter "do"
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        def badDoParameter(headers, auth):
            personId, photoId = self.createPersonAndDescriptor(headers)
            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "dettach")
            self.assertErrorRestAnswer(replyInfo, 400, Error.BadQueryParams, auth = authStr(auth), msgFormat = ["do"])

        badDoParameter()
