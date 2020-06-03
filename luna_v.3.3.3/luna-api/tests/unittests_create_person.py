from crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase, authStr
from tests.functions import checkUUID4
from tests import luna_api_functions


class TestCreatePerson(TestBase):
    """
    Tests creating person
    """

    def setUp(self):
        self.createAccountAndToken()

    def test_person_create_person(self):
        """
        .. test:: test_person_create_person

            :resources: "/storage/persons"
            :description: success creating person
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def createPersonTest(headers, auth):
            replyInfo = luna_api_functions.createPerson(headers)
            self.assertEqual(replyInfo.statusCode, 201, authStr(auth))
            self.assertTrue("person_id" in replyInfo.body, authStr(auth))
            self.assertTrue(checkUUID4(replyInfo.body["person_id"]), authStr(auth))

        createPersonTest()

    def test_person_create_person_with_data(self):
        """
        .. test:: test_person_create_person_with_data

            :resources: "/storage/persons"
            :description: success creating person with user_data
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def createPersonTest_withData(headers, auth):
            replyInfo = luna_api_functions.createPerson(headers, "petya 123")
            self.assertEqual(replyInfo.statusCode, 201, authStr(auth))
            self.assertTrue("person_id" in replyInfo.body, authStr(auth))
            self.assertTrue(checkUUID4(replyInfo.body["person_id"]), authStr(auth))

        createPersonTest_withData()

    def test_person_create_with_too_long_external_id(self):
        """
        .. test:: test_person_create_with_too_long_external_id

            :resources: "/storage/persons"
            :description: failure create person with too long external id
            :LIS: No
            :tag: Person action
        """
        @self.authorization
        def createPersonTest_withExternalId(headers, auth):
            replyInfo = luna_api_functions.createPerson(headers, userData="petya 123", externalId="x" * 37)
            self.assertEqual(replyInfo.statusCode, 400, auth)
            self.assertEqual(replyInfo.body['error_code'], Error.BadInputJson.errorCode, auth)

        createPersonTest_withExternalId()


    def test_person_create_person_with_maximum_data(self):
        """
        .. test:: test_person_create_person_with_maximum_data

            :resources: "/storage/persons"
            :description: try creating person with maximum user_data length
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def createPerson_maxUserInfoTest(headers, auth):
            userData = "x" * 128
            replyInfo = luna_api_functions.createPerson(headers, userData)
            self.assertEqual(replyInfo.statusCode, 201, authStr(auth))
            self.assertTrue("person_id" in replyInfo.body, authStr(auth))
            self.assertTrue(checkUUID4(replyInfo.body["person_id"]), authStr(auth))

        createPerson_maxUserInfoTest()

    def test_person_create_person_with_large_data(self):
        """
        .. test:: test_person_create_person_with_large_data

            :resources: "/storage/persons"
            :description: try creating person with big user_data
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def createPerson_bigUserInfoTest(headers, auth):
            userData = "x" * 129
            replyInfo = luna_api_functions.createPerson(headers, userData)
            self.assertErrorRestAnswer(replyInfo, 400, Error.BigUserData, auth=auth)

        createPerson_bigUserInfoTest()

    def test_person_create_person_with_bad_type_data(self):
        """
        .. test:: test_person_create_person_with_bad_type_data

            :resources: "/storage/persons"
            :description: try creating person with bad type of user data (int)
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def createPerson_bigUserInfoTest(headers, auth):
            userData = 123
            replyInfo = luna_api_functions.createPerson(headers, userData)
            self.assertErrorRestAnswer(replyInfo, 400, Error.BadTypeOfFieldInJSON,
                                       msgFormat=['user_data', 'string'], auth=auth)

        createPerson_bigUserInfoTest()

    def test_person_create_person_with_external_id(self):
        """
        .. test:: test_person_create_person_with_external_id

            :resources: "/storage/persons"
            :description: success creating person with external_id
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def createPersonTest_withExternalId(headers, auth):
            replyInfo = luna_api_functions.createPerson(headers, externalId="test external id")
            self.assertEqual(replyInfo.statusCode, 201, authStr(auth))
            self.assertTrue("person_id" in replyInfo.body, authStr(auth))
            self.assertTrue(checkUUID4(replyInfo.body["person_id"]), authStr(auth))

        createPersonTest_withExternalId()

    def test_person_create_person_with_maximum_external_id(self):
        """
        .. test:: test_person_create_person_with_maximum_external_id

            :resources: "/storage/persons"
            :description: try creating person with maximum external_id length
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def createPerson_maxExternalIdTest(headers, auth):
            externalId = "x" * 36
            replyInfo = luna_api_functions.createPerson(headers, externalId=externalId)
            self.assertEqual(replyInfo.statusCode, 201, authStr(auth))
            self.assertTrue("person_id" in replyInfo.body, authStr(auth))
            self.assertTrue(checkUUID4(replyInfo.body["person_id"]), authStr(auth))

        createPerson_maxExternalIdTest()

    def test_person_create_person_with_large_external_id(self):
        """
        .. test:: test_person_create_person_with_large_external_id

            :resources: "/storage/persons"
            :description: try creating person with big external_id
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def createPerson_bigExternalIdTest(headers, auth):
            externalId = "x" * 129
            replyInfo = luna_api_functions.createPerson(headers, externalId=externalId)
            self.assertErrorRestAnswer(replyInfo, 400, Error.BigExternalId, auth=auth)

        createPerson_bigExternalIdTest()

    def test_person_create_person_with_bad_type_external_id(self):
        """
        .. test:: test_person_create_person_with_bad_type_external_id

            :resources: "/storage/persons"
            :description: try creating person with bad type of external_id (int)
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def createPerson_bigUserInfoTest(headers, auth):
            externalId = 123
            replyInfo = luna_api_functions.createPerson(headers, externalId=externalId)
            self.assertErrorRestAnswer(replyInfo, 400, Error.BadTypeOfFieldInJSON,
                                       msgFormat=['external_id', 'string'], auth=auth)

        createPerson_bigUserInfoTest()

    def test_person_create_person_without_user_data_and_external_id(self):
        """
        .. test:: test_person_create_person_without_user_data_and_external_id

            :resources: "/storage/persons"
            :description: try creating person without user data and external id
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def createPerson_WithoutDataAndExternalIdTest(headers, auth):
            replyInfo = luna_api_functions.createPerson(headers)
            self.assertEqual(replyInfo.statusCode, 201)
            personId = replyInfo.body['person_id']
            replyInfo = luna_api_functions.getPerson(headers, personId=personId)
            self.assertEqual(replyInfo.body['user_data'], '')
            self.assertEqual(replyInfo.body['external_id'], None)

        createPerson_WithoutDataAndExternalIdTest()
