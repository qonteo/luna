from tests.classes import TestBase, authStr
from tests.functions import checkUUID4
from collections import namedtuple
from tests import luna_api_functions
from uuid import uuid4
import unittest
from crutches_on_wheels.errors.errors import Error


class TestGetPersons(TestBase):
    """
    Tests getting persons
    """
    def setUp(self):
        self.createAccountAndToken()

    def test_person_get_persons(self):
        """
        .. test:: test_person_get_persons

            :resources: "/storage/persons"
            :description: success getting person and check response json
            :LIS: No
            :tag: Person action
        """
        @self.authorization
        def getPersonsTest(headers, auth):
            userData = "some user data"
            replyInfo = luna_api_functions.createPerson(headers, userData)
            self.assertEqual(replyInfo.statusCode, 201, authStr(auth))
            person_id = replyInfo.body["person_id"]
            self.assertTrue(checkUUID4(person_id), authStr(auth))
            page = 1
            pageSize = 1
            replyInfo = luna_api_functions.getPersons(headers, page, pageSize)
            self.assertGetPersons(replyInfo, auth)
            self.assertEqual(pageSize, len(replyInfo.body["persons"]), authStr(auth))
            personInfo = replyInfo.body["persons"][0]
            self.assertEqual(person_id, personInfo["id"], authStr(auth))
            self.assertEqual(userData, personInfo["user_data"], authStr(auth))

        getPersonsTest()

    def test_person_get_persons_with_page_size(self):
        """
        .. test:: test_person_get_persons_with_page_size

            :resources: "/storage/persons"
            :description: success getting person with different number of page_size
            :LIS: No
            :tag: Person action
        """
        @self.authorization
        def getPersonsPageSizeTest(headers, auth):
            self.createPersons(headers, 101)
            page = 1
            pageSizeType = namedtuple("PageSizeType", "queryParamsPageSize expectedPageSize")
            pageSizes = (pageSizeType(1, 1),
                         pageSizeType(10, 10),
                         pageSizeType(100, 100),
                         pageSizeType(-1, 1),
                         pageSizeType(101, 100))
            for pageSize in pageSizes:
                with self.subTest(page_size = pageSize):
                    replyInfo = luna_api_functions.getPersons(headers, page, pageSize.queryParamsPageSize)
                    self.assertGetPersons(replyInfo, auth)
                    self.assertEqual(pageSize.expectedPageSize, len(replyInfo.body["persons"]), authStr(auth))

        getPersonsPageSizeTest()

    def test_person_get_persons_order(self):
        """
        .. test:: test_person_get_persons_order

            :resources: "/storage/persons"
            :description: testing order of persons
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def getPersonsOrderTest(headers, auth):
            personsCount = 3
            personIds = self.createPersons(headers, personsCount)
            replyInfo = luna_api_functions.getPersons(headers, page_size=personsCount)
            self.assertGetPersons(replyInfo, auth)
            for idx, personId in enumerate(personIds):
                with self.subTest(personId = personId):
                    self.assertEqual(personId, replyInfo.body["persons"][personsCount - 1 - idx]["id"], authStr(auth))

        getPersonsOrderTest()

    def test_person_get_persons_with_page(self):
        """
        .. test:: test_person_get_persons_with_page

            :resources: "/storage/persons"
            :description: success getting person with different number of page
            :LIS: No
            :tag: Person action
        """
        @self.authorization
        def getPersonsPageTest(headers, auth):
            pagesCount = (-1, 0, 1)
            pageSize = 1
            for page in pagesCount:
                with self.subTest(page = page):
                    replyInfo = luna_api_functions.getPersons(headers, page, pageSize)
                    self.assertGetPersons(replyInfo, auth)

        getPersonsPageTest()

    def test_person_get_person_by_part_user_data(self):
        """
        .. test:: test_person_get_person_by_part_user_data

            :resources: "/storage/persons/\{person_id\}"
            :description: success getting person by part of user_data
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def getPersonPartDataTest(headers, auth):
            userData = str(uuid4())
            personId = luna_api_functions.createPerson(headers, userData=userData, raiseError=True).body['person_id']
            replyInfo = luna_api_functions.getPersons(headers, userData=userData[2:-2])
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertEqual(replyInfo.body['count'], 1, authStr(auth))
            self.assertEqual(replyInfo.body['persons'][0]["id"], personId, authStr(auth))
            self.assertEqual(replyInfo.body['persons'][0]["user_data"], userData, authStr(auth))

        getPersonPartDataTest()

    def test_person_get_person_by_user_data(self):
        """
        .. test:: test_person_get_person_by_user_data

            :resources: "/storage/persons/\{person_id\}"
            :description: success getting person by user_data
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def getPersonDataTest(headers, auth):
            userData = str(uuid4())
            personId = luna_api_functions.createPerson(headers, userData=userData, raiseError=True).body['person_id']
            replyInfo = luna_api_functions.getPersons(headers, userData=userData)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertEqual(replyInfo.body['count'], 1, authStr(auth))
            self.assertEqual(replyInfo.body['persons'][0]["id"], personId, authStr(auth))
            self.assertEqual(replyInfo.body['persons'][0]["user_data"], userData, authStr(auth))

        getPersonDataTest()

    @unittest.skip('There are some null values in db at the moment')
    def test_person_get_person_by_empty_user_data(self):
        """
        .. test:: test_person_get_person_by_empty_user_data

            :resources: "/storage/persons/\{person_id\}"
            :description: success getting person by empty user_data
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def getPersonEmptyDataTest(headers, auth):
            replyInfoUserData = luna_api_functions.getPersons(headers, userData='')
            replyInfo = luna_api_functions.getPersons(headers, raiseError=True)
            self.assertEqual(replyInfoUserData.statusCode, 200, authStr(auth))
            self.assertGreaterEqual(replyInfoUserData.body['count'], 1, authStr(auth))
            self.assertEqual(replyInfoUserData.body['count'], replyInfo.body['count'])

        getPersonEmptyDataTest()

    def test_person_get_person_by_max_user_data(self):
        """
        .. test:: test_person_get_person_by_max_user_data

            :resources: "/storage/persons/\{person_id\}"
            :description: success getting person by user_data with max-size user_data
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def getPersonMaxDataTest(headers, auth):
            userData = str(uuid4()) + 'x' * (128-36)
            personId = luna_api_functions.createPerson(headers, userData=userData, raiseError=True).body['person_id']
            replyInfo = luna_api_functions.getPersons(headers, userData=userData)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertEqual(replyInfo.body['count'], 1, authStr(auth))
            self.assertEqual(replyInfo.body['persons'][0]["id"], personId, authStr(auth))
            self.assertEqual(replyInfo.body['persons'][0]["user_data"], userData, authStr(auth))

        getPersonMaxDataTest()

    def test_person_get_person_by_big_user_data(self):
        """
        .. test:: test_person_get_person_by_big_user_data

            :resources: "/storage/persons/\{person_id\}"
            :description: success getting person by user_data with size more than max size
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def getPersonBigDataTest(headers, auth):
            userData = str(uuid4()) + 'x' * (128-36+1)
            replyInfo = luna_api_functions.createPerson(headers, userData=userData)
            self.assertErrorRestAnswer(replyInfo, 400, Error.BigUserData, auth=authStr(auth))

        getPersonBigDataTest()

    def test_person_get_person_by_bad_format_user_data(self):
        """
        .. test:: test_person_get_person_by_bad_format_user_data

            :resources: "/storage/persons/\{person_id\}"
            :description: success getting person by user_data in bad format
            :LIS: No
            :tag: Person action
        """

        @self.authorization
        def getPersonBadFormatDataTest(headers, auth):
            replyInfo = luna_api_functions.createPerson(headers, userData=123)
            self.assertErrorRestAnswer(replyInfo, 400, Error.BadTypeOfFieldInJSON, msgFormat=['user_data', 'string'],
                                       auth=authStr(auth))

        getPersonBadFormatDataTest()

    def assertGetPersons(self, replyInfo, auth):
        self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
        self.assertTrue("persons" in replyInfo.body, authStr(auth))
        self.assertTrue("count" in replyInfo.body, authStr(auth))