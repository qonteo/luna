import uuid

from crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase, authStr
from tests.functions import checkUUID4
from tests import luna_api_functions


class TestList(TestBase):
    """
    Tests of creating account list and work with it (get, patch, delete)
    """

    def setUp(self):
        self.createAccountAndToken()

    def test_lists_create_list(self):
        """
        .. test:: test_lists_create_list

            :resources: "/storage/lists"
            :description: success creating account lists
            :LIS: No
            :tag: List action
        """
        @self.authorization
        def getCreateListTest(headers, auth):
            for typeList in [True, False]:
                replyInfo = luna_api_functions.createList(headers, typeList)
                self.assertEqual(replyInfo.statusCode, 201, authStr(auth))
                self.assertTrue("list_id" in replyInfo.body, authStr(auth))
                self.assertTrue(checkUUID4(replyInfo.body["list_id"]), authStr(auth))

        getCreateListTest()

    def test_lists_create_list_with_data(self):
        """
        .. test:: test_lists_create_list_with_data

            :description: success creating account lists with list_data (descriptors and persons)
            :resources: "/storage/lists"
            :LIS: No
            :tag: List action
        """
        @self.authorization
        def getCreateListTest(headers, auth):
            data = "DATA in list"
            for typeList in [True, False]:
                replyInfo = luna_api_functions.createList(headers, typeList, data)
                self.assertEqual(replyInfo.statusCode, 201, authStr(auth))
                self.assertTrue("list_id" in replyInfo.body, authStr(auth))
                self.assertTrue(checkUUID4(replyInfo.body["list_id"]), authStr(auth))
                listId = replyInfo.body["list_id"]

                reply = luna_api_functions.getList(headers, listId)
                self.assertEqual(data, reply.body["list_data"], authStr(auth))

        getCreateListTest()

    def test_lists_get_lists(self):
        """
        .. test:: test_lists_get_lists

            :description: success getting all lists (descriptors and persons)
            :resources: "/storage/lists"
            :LIS: No
            :tag: List action
        """
        @self.authorization
        def getListTest(headers, auth):
            for typeList in [True, False]:
                replyInfo = luna_api_functions.createList(headers, typeList)
                list1 = replyInfo.body["list_id"]
                replyInfo = luna_api_functions.createList(headers, typeList)
                list2 = replyInfo.body["list_id"]

                reply = luna_api_functions.getLists(headers)
                self.assertEqual(reply.statusCode, 200)
                self.assertTrue("lists" in reply.body, authStr(auth))
                self.assertTrue("descriptor_lists" in reply.body["lists"], authStr(auth))
                self.assertTrue("person_lists" in reply.body["lists"], authStr(auth))
                if typeList:
                    typeName = "person_lists"
                else:
                    typeName = "descriptor_lists"

        getListTest()

    def test_lists_get_lists_with_pagination(self):
        """
        .. test:: test_token_get_list_tokens

            :resources: "/account/tokens"
            :description: success getting account tokens with pagination
            :LIS: No
            :tag: Account actions
        """

        @self.authorization
        def getListTest(headers, auth):
            for _ in range(4):
                luna_api_functions.createList(headers, True, "test_lists_get_lists_with_pagination_desc")
                luna_api_functions.createList(headers, False, "test_lists_get_lists_with_pagination_persons")

            replyInfo1 = luna_api_functions.getLists(headers, pageSize=2, page=1)
            self.assertEqual(2, len(replyInfo1.body["lists"]["person_lists"]))
            replyInfo2 = luna_api_functions.getLists(headers, pageSize=2, page=2)
            self.assertEqual(2, len(replyInfo2.body["lists"]["descriptor_lists"]))
            self.assertTrue(replyInfo2.body["lists"]["person_lists"][0]["id"] != replyInfo1.body["lists"]["person_lists"][0]["id"])

        getListTest()

    def test_lists_create_list_with_bad_auth(self):
        """
        .. test:: test_lists_create_list_with_bad_auth

            :description: try creating account lists (descriptors and persons) with bad auth data
            :resources: "/storage/lists"
            :LIS: No
            :tag: List action
        """
        def badAuthTest():
            for typeList in [True, False]:
                headers = {'login': self.email, 'password': "ddd"}
                replyInfo = luna_api_functions.createList(headers, typeList)
                self.assertErrorRestAnswer(replyInfo, 401, Error.AccountNotFound)

                headers = {'login': "test@test.ru", 'password': self.password}
                replyInfo = luna_api_functions.createList(headers, typeList)
                self.assertErrorRestAnswer(replyInfo, 401, Error.AccountNotFound)

                headers = {'token': str(uuid.uuid4())}
                replyInfo = luna_api_functions.createList(headers, typeList)
                self.assertErrorRestAnswer(replyInfo, 401, Error.AccountNotFound)

                headers = {'token': "test"}
                replyInfo = luna_api_functions.createList(headers, typeList)
                self.assertErrorRestAnswer(replyInfo, 401, Error.BadFormatUUID)

                headers = {}

        badAuthTest()

    def test_lists_delete_lists(self):
        """
        .. test:: test_lists_delete_lists

            :description: success removing account lists (descriptors and persons)
            :resources: "/storage/lists"
            :LIS: No
            :tag: List action
        """
        @self.authorization
        def deleteListTest(headers, auth):
            replyInfo = luna_api_functions.createList(headers, True)
            list_id = replyInfo.body["list_id"]
            replyInfo = luna_api_functions.deleteLists(headers, [list_id])
            self.assertEqual(replyInfo.statusCode, 204)
            replyInfo = luna_api_functions.getLists(headers)
            self.assertTrue(not (list_id in replyInfo.body["lists"]), authStr(auth))

        deleteListTest()

    def test_lists_delete_list_empty_json(self):
        """
        .. test:: test_lists_create_list_with_bad_auth

            :description: try removing account lists without json(descriptors and persons)
            :resources: "/storage/lists"
            :LIS: No
            :tag: List action
        """

        @self.authorization
        def deleteListEJTest(headers, auth):
            replyInfo = luna_api_functions.manualRequest('/storage/lists', 'DELETE', headers = headers)
            self.assertErrorRestAnswer(replyInfo, 400, Error.EmptyJson, auth = authStr(auth))

        deleteListEJTest()

    def test_lists_delete_list_bad_key_in_json(self):
        """
        .. test:: test_lists_delete_list_bad_key_in_json

            :description: try removing account lists with wrong key in json("list_id" instead "lists")
            :resources: "/storage/lists"
            :LIS: No
            :tag: List action
        """

        @self.authorization
        def deleteListBadFJ(headers, auth):
            replyInfo = luna_api_functions.createList(headers, True)
            list1 = replyInfo.body["list_id"]
            payload = {"list_id": [list1]}
            replyInfo = luna_api_functions.manualRequest('/storage/lists', 'DELETE', headers = headers, body = payload)
            self.assertErrorRestAnswer(replyInfo, 400, Error.FieldNotInJSON, ["lists"], auth = authStr(auth))

        deleteListBadFJ()

    def test_lists_delete_list_bad_value_type_in_json(self):
        """
        .. test:: test_lists_delete_list_bad_value_type_in_json

            :description: try removing account lists with wrong type value in json("list_id" instead lists of list_id)
            :resources: "/storage/lists"
            :LIS: No
            :tag: List action
        """
        @self.authorization
        def deleteListBadFT(headers, auth):
            for typeList in [True, False]:
                replyInfo = luna_api_functions.createList(headers, typeList)
                list1 = replyInfo.body["list_id"]
                payload = {"lists": list1}
                reply = luna_api_functions.manualRequest('/storage/lists', 'DELETE', body = payload)
                self.assertErrorRestAnswer(reply, 400, Error.BadTypeOfFieldInJSON, ["lists", "list"],
                                           auth = authStr(auth))

        deleteListBadFT()

    def test_list_delete_list_by_id(self):
        """
        .. test:: test_list_delete_list_by_id

            :description: try removing account lists by id
            :resources: "/storage/lists/\{list_id\}"
            :LIS: No
            :tag: List action
        """
        @self.authorization
        def testDeleteListById(headers, auth):
            for typeList in [True, False]:
                replyInfo = luna_api_functions.createList(headers, typeList)
                list1 = replyInfo.body["list_id"]
                replyInfo = luna_api_functions.createList(headers, typeList)
                list_id = replyInfo.body["list_id"]
                replyInfo = luna_api_functions.deleteList(headers, list_id)
                self.assertEqual(replyInfo.statusCode, 204)
                replyInfo = luna_api_functions.getList(headers, list_id)
                self.assertErrorRestAnswer(replyInfo, 404, Error.ListNotFound, authStr(auth) +
                                           ", type list: {}".format(typeList))
                replyInfo = luna_api_functions.getList(headers, list1)
                self.assertEqual(replyInfo.statusCode, 200, "{}, type list: {}".format(authStr(auth), typeList))
        testDeleteListById()

    def test_list_patch_list_with_data(self):
        """
        .. test:: test_list_patch_list_with_data

            :description: patch data of list
            :resources: "/storage/lists/\{list_id\}"
            :LIS: No
            :tag: List action
        """
        @self.authorization
        def getPatchListTest(headers, auth):
            data = "DATA in list"
            newData = "New DATA in list"
            for typeList in [True, False]:
                replyInfo = luna_api_functions.createList(headers, typeList, data)
                self.assertEqual(replyInfo.statusCode, 201, authStr(auth))
                self.assertTrue("list_id" in replyInfo.body, authStr(auth))
                self.assertTrue(checkUUID4(replyInfo.body["list_id"]), authStr(auth))
                listId = replyInfo.body["list_id"]

                reply = luna_api_functions.getLists(headers)

                if typeList:
                    typeName = "person_lists"
                else:
                    typeName = "descriptor_lists"

                for objectList in reply.body["lists"][typeName]:
                    if objectList["id"] == listId:
                        self.assertEqual(data, objectList["list_data"], authStr(auth))

                luna_api_functions.patchListData(headers, listId, newData)
                reply = luna_api_functions.getLists(headers)

                for objectList in reply.body["lists"][typeName]:
                    if objectList["id"] == listId:
                        self.assertEqual(newData, objectList["list_data"], authStr(auth))

        getPatchListTest()

#: TODO tests for getting list by id
#: TODO tests to access to non exist list
