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
            self.assertErrorRestAnswer(replyInfo, 400, Error.BigUserData, auth = auth)

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
                                       msgFormat = ['user_data', 'string'], auth = auth)

        createPerson_bigUserInfoTest()
