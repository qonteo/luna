from crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase, authStr
from tests.resources import standardImage
from tests import luna_api_functions
from uuid import uuid4


class TestPerson(TestBase):
    """
    Tests action with person
    """

    def setUp(self):
        self.createAccountAndToken()
        headers = luna_api_functions.createAuthHeader()
        self.userData = "testData"
        self.externalId = 'test external id'
        replyInfo = luna_api_functions.createPerson(headers, userData=self.userData, externalId=self.externalId)
        self.personId = replyInfo.body["person_id"]

    def test_person_get_user_data(self):
        """
        .. test:: test_person_get_person_data

            :resources: "/storage/persons/\{person_id\}"
            :description: success getting user_data of person by id
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def getPersonDataTest(headers, auth):
            replyInfo = luna_api_functions.getPerson(headers, self.personId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertEqual(replyInfo.body["user_data"], self.userData, authStr(auth))

        getPersonDataTest()

    def test_person_get_user_data_non_exist_person(self):
        """
        .. test:: test_person_get_person_data_non_exist_person

            :resources: "/storage/persons/\{person_id\}"
            :description: try getting user_data of person by non exist person_id
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def getPersonDataBITest(headers, auth):
            reply = luna_api_functions.getPerson(headers, str(uuid4()))
            self.assertErrorRestAnswer(reply, 404, Error.PersonNotFound, auth=authStr(auth))

        getPersonDataBITest()

    def test_person_patch_user_data(self):
        """
        .. test:: test_person_patch_user_data

            :resources: "/storage/persons/\{person_id\}"
            :description: success patching user_data of person by id
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def updatePersonData(headers, auth):
            replyInfo = luna_api_functions.patchPerson(headers, self.personId, "newTestData")
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getPerson(headers, self.personId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertEqual(replyInfo.body["user_data"], "newTestData", authStr(auth))
            self.assertEqual(replyInfo.body["external_id"], self.externalId, authStr(auth))

        updatePersonData()

    def test_person_get_person_external_id(self):
        """
        .. test:: test_person_get_person_external_id

            :resources: "/storage/persons/\{person_id\}"
            :description: success getting external id of person by person id
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def getPersonExternalId(headers, auth):
            replyInfo = luna_api_functions.getPerson(headers, self.personId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertEqual(replyInfo.body["external_id"], self.externalId, authStr(auth))

        getPersonExternalId()

    def test_person_patch_external_id(self):
        """
        .. test:: test_person_patch_external_id

            :resources: "/storage/persons/\{person_id\}"
            :description: success patching external id of person by id
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def updatePersonExternalId(headers, auth):
            externalId = 'test external id 2'
            replyInfo = luna_api_functions.patchPerson(headers, self.personId, externalId=externalId)
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getPerson(headers, self.personId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertEqual(replyInfo.body["external_id"], externalId, authStr(auth))
            self.assertEqual(replyInfo.body["user_data"], self.userData, authStr(auth))

        updatePersonExternalId()

    def test_person_patch_user_data_and_external_id(self):
        """
        .. test:: test_person_patch_user_data_and_external_id

            :resources: "/storage/persons/\{person_id\}"
            :description: success patching  user  data and external id
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def updatePersonUserDataAndExternalId(headers, auth):
            userData = 'testUserData 3'
            externalId = 'test external id 3'

            replyInfo = luna_api_functions.patchPerson(headers, self.personId, userData=userData,
                                                       externalId=externalId)
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getPerson(headers, self.personId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))

            self.assertEqual(replyInfo.body["user_data"], userData, authStr(auth))
            self.assertEqual(replyInfo.body["external_id"], externalId, authStr(auth))

        updatePersonUserDataAndExternalId()

    def test_person_delete_person(self):
        """
        .. test:: test_person_delete_person

            :resources: "/storage/persons/\{person_id\}"
            :description: success removing person by id
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def deletePersonWithListAndPhoto(headers, auth):
            personId = luna_api_functions.createPerson(headers, "img and list").body["person_id"]

            replyInfo = luna_api_functions.getPerson(headers, personId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage)
            photoId = replyInfo.body["faces"][0]["id"]

            replyInfo = luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, 'attach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.createList(headers)
            list_id = replyInfo.body["list_id"]
            replyInfo = luna_api_functions.linkListToPerson(headers, personId, list_id, 'attach')
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))

            replyInfo = luna_api_functions.deletePerson(headers, personId)
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))

            replyInfo = luna_api_functions.getPerson(headers, personId)
            self.assertErrorRestAnswer(replyInfo, 404, Error.PersonNotFound, auth=authStr(auth))

        deletePersonWithListAndPhoto()

    def test_person_delete_person_without_photo(self):
        """
        .. test:: test_person_delete_person_without_photo

            :resources: "/storage/persons/\{person_id\}"
            :description: success removing person by id without photo
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def deletePersonWithoutPhotoTest(headers, auth):
            replyInfo = luna_api_functions.createPerson(headers)
            personId = replyInfo.body["person_id"]
            replyInfo = luna_api_functions.getPerson(headers, personId)
            self.assertEqual(replyInfo.statusCode, 200)
            replyInfo = luna_api_functions.deletePerson(headers, personId)
            self.assertEqual(replyInfo.statusCode, 204, authStr(auth))
            replyInfo = luna_api_functions.getPerson(headers, personId)
            self.assertErrorRestAnswer(replyInfo, 404, Error.PersonNotFound, auth=authStr(auth))

        deletePersonWithoutPhotoTest()

    def test_person_get_nonexists_person(self):
        """
        .. test:: test_person_get_nonexists_person

            :resources: "/storage/persons/\{person_id\}"
            :description: get non exists person by person id
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def getPersonExternalId(headers, auth):
            replyInfo = luna_api_functions.getPerson(headers, personId=str(uuid4()))
            self.assertEqual(replyInfo.statusCode, 404, authStr(auth))
            self.assertErrorRestAnswer(replyInfo, 404, Error.PersonNotFound, auth=authStr(auth))

        getPersonExternalId()
