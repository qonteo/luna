import unittest
from tests.functions import checkUUID4
from tests.resources import warpedImage
from tests import luna_api_functions
from tests.config import TEST_EMAIL, TEST_PASSWORD, TEST_ORGANIZATION_NAME

authArr = ["token", "basic"]


def authStr(authType):
    return "Authorization type: " + authType


class TestBase(unittest.TestCase):
    def authorization(self, func):
        def wrap(*func_args, **func_kwargs):
            for auth in authArr:
                with self.subTest(auth=auth):
                    if auth == "basic":
                        headers = luna_api_functions.createAuthHeader('login')
                    else:
                        headers = luna_api_functions.createAuthHeader('token', self.token)
                    func(headers, self.token, *func_args, **func_kwargs)
            return

        return wrap

    def assertErrorRestAnswer(self, reply, statusCode, error, msgFormat=None, auth=""):
        self.assertEqual(reply.statusCode, statusCode)
        if msgFormat is None:
            self.assertEqual(reply.body["detail"], error.detail, auth)
        else:
            self.assertEqual(reply.body["detail"],
                             error.detail.format(*msgFormat), auth)
        self.assertEqual(reply.body["error_code"],
                         error.errorCode, auth)

    def assertSuccessStorageDescriptor(self, reply, auth):
        self.assertEqual(reply.statusCode, 201, auth)
        self.assertTrue("faces" in reply.body, auth)

    def assertSuccessExtractPhoto(self, reply, auth):
        self.assertEqual(reply.statusCode, 201, auth)
        self.assertTrue("faces" in reply.body, auth)
        faces = reply.body["faces"]
        for face in faces:
            self.assertTrue("id" in face, auth)
            self.assertTrue(checkUUID4(face["id"]), auth)

    def assertResultMatching(self, candidate, auth, isPersons=True):
        if isPersons:
            nameId = "person_id"
            self.assertIn('external_id', candidate, auth)
            self.assertTrue('test-external-id' == candidate['external_id'], auth)
            self.assertIn('user_data', candidate, auth)
            self.assertTrue('test user data' == candidate['user_data'], auth)
        else:
            nameId = "id"
        self.assertTrue(nameId in candidate, auth)
        self.assertTrue(checkUUID4(candidate[nameId]), auth)
        self.assertTrue("similarity" in candidate, auth)
        self.assertTrue(0 <= candidate["similarity"] <= 1, auth)

    def assertSuccessMatching(self, reply, auth, isPersons=True):
        self.assertEqual(reply.statusCode, 201, auth)
        self.assertTrue("candidates" in reply.body, auth)
        candidates = reply.body["candidates"]
        for candidate in candidates:
            self.assertResultMatching(candidate, auth, isPersons)

    def createAccount(self):
        self.password = TEST_PASSWORD
        self.email = TEST_EMAIL
        self.organization_name = TEST_ORGANIZATION_NAME
        luna_api_functions.registration()

    def createAccountAndToken(self):
        self.createAccount()
        reply = luna_api_functions.createToken(self.email, self.password)
        self.token = reply.body["token"]

    @staticmethod
    def createPerson(headers):
        replyInfo = luna_api_functions.createPerson(headers, userData='test user data', externalId="test-external-id")
        return replyInfo.body["person_id"]

    @staticmethod
    def createPersons(headers, personsCount):
        personIds = []
        for _ in range(personsCount):
            reply = luna_api_functions.createPerson(headers)
            personIds.append(reply.body["person_id"])
        return tuple(personIds)

    @staticmethod
    def createPersonWithList(headers):
        personId = TestBase.createPerson(headers)
        accountList = TestBase.createList(headers, True)
        TestBase.linkPersonToList(headers, accountList, personId)
        return personId

    @staticmethod
    def createPersonWithPhoto(headers):
        personId = TestBase.createPerson(headers)
        photoId = TestBase.createPhoto(headers)
        TestBase.linkPersonToPhoto(headers, photoId, personId)
        return personId

    @staticmethod
    def createList(headers, isPersonList=True):
        replyInfo = luna_api_functions.createList(headers, isPersonList, listData="test")
        return replyInfo.body["list_id"]

    @staticmethod
    def createPhoto(headers):
        replyInfo = luna_api_functions.extractDescriptors(headers, filename=warpedImage, warpedImage=True)
        return replyInfo.body["faces"][0]["id"]

    @staticmethod
    def linkPersonToList(headers, listId, personId):
        luna_api_functions.linkListToPerson(headers, personId, listId, "attach")

    @staticmethod
    def linkPersonToPhoto(headers, photoId, personId):
        luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
