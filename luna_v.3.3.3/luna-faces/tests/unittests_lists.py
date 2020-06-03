from tests.classes import TestBase
from uuid import uuid4
from luna_faces.crutches_on_wheels.errors.errors import Error
from tests.shemas import SHEMA_CREATE_LIST, SHEMA_GET_LISTS, SCHEMA_OPTIONS_LISTS

DEFAULT_LISTS_COUNT = 3
PAGE_SIZE = 100


class TestLists(TestBase):
    """
    Test Lists
    """
    def setUp(self):
        TestBase.setUp(self)
        self.listIds = []
        for _ in range(DEFAULT_LISTS_COUNT):
            listId = self.FacesApi.createList(self.account_id, self.user_data, raiseError=True).json['list_id']
            self.listIds.append(listId)
            self.lists.append(listId)

    def check_status_json_and_options_lists(self, reply, lists):
        """
        For options method function check status code, json and lists equal
        Args:
            reply: reply
            lists: list of dicts with list id, link and unlink keys
        """
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_OPTIONS_LISTS)
        self.assertListEqual(reply.json['lists'], lists, reply.text)

    def test_create_list(self):
        """
            :description: Create list.
            :resources: '/lists'
        """
        reply = self.FacesApi.createList(self.account_id, self.user_data)
        self.lists.append(reply.json['list_id'])
        self.assertEqual(reply.statusCode, 201)
        self.validateJson(reply.json, SHEMA_CREATE_LIST)

    def test_create_list_max_userdata(self):
        """
            :description: Create list with max size of user_data.
            :resources: '/lists'
        """
        reply = self.FacesApi.createList(self.account_id, 'x'*128)
        self.lists.append(reply.json['list_id'])
        self.assertEqual(reply.statusCode, 201)
        self.validateJson(reply.json, SHEMA_CREATE_LIST)

    def test_create_list_excessive_userdata(self):
        """
            :description: Create list with user_data with size > max.
            :resources: '/lists'
        """
        reply = self.FacesApi.createList(self.account_id, 'x'*129)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', '\''+'x'*129+'\''+' is too long'])

    def test_create_list_badformat_userdata(self):
        """
            :description: Create list with bad format user data.
            :resources: '/lists'
        """
        badUserData = 123
        reply = self.FacesApi.createList(self.account_id, badUserData)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', str(badUserData) + ' is not of type \'string\''])

    def test_create_list_badformat_accountid(self):
        """
            :description: Create list with bad format accountId.
            :resources: '/lists'
        """
        badAccountId = 123
        reply = self.FacesApi.createList(badAccountId, self.user_data)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_get_lists(self):
        """
            :description: Get lists.
            :resources: '/lists'
        """
        reply = self.FacesApi.getLists()
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_LISTS)

    def test_get_lists_partuserdata(self):
        """
            :description: Get lists.
            :resources: '/lists'
        """
        reply = self.FacesApi.getLists(self.user_data[:len(self.user_data)//2])
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_LISTS)

    def test_get_lists_accountid(self):
        """
            :description: Get lists with accountID.
            :resources: '/lists'
        """
        self.listId = self.FacesApi.createList(str(uuid4()), self.user_data).json['list_id']
        self.lists.append(self.listId)
        reply = self.FacesApi.getLists(accountId=self.account_id)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_LISTS)
        replyListIds = [listId['list_id'] for listId in reply.json['lists']]
        for listId in self.listIds:
            self.assertIn(listId, replyListIds)
        self.assertNotIn(self.listId, replyListIds)

    def test_get_lists_nonexists_accountid(self):
        """
            :description: Get lists with nonexists accountID.
            :resources: '/lists'
        """
        reply = self.FacesApi.getLists(accountId=str(uuid4()))
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_LISTS)
        self.assertEqual(reply.json['count'], 0)

    def test_get_lists_badformat_accountid(self):
        """
            :description: Get lists with bad format accountID.
            :resources: '/lists'
        """
        badAccountId = 123
        reply = self.FacesApi.getLists(accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_get_lists_page_pagesize(self):
        """
            :description: Get lists with max page_size.
            :resources: '/lists'
        """
        reply = self.FacesApi.getLists(page=1, pageSize=100)
        self.validateJson(reply.json, SHEMA_GET_LISTS)
        self.assertEqual(reply.statusCode, 200)
        self.assertGreaterEqual(reply.json['count'], DEFAULT_LISTS_COUNT)

    def test_get_lists_page(self):
        """
            :description: Get lists with page=-1.
            :resources: '/lists'
        """
        reply = self.FacesApi.getLists(page=-1, pageSize=100)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_LISTS)
        self.assertGreaterEqual(reply.json['count'], DEFAULT_LISTS_COUNT)

    def test_get_lists_bad_pagesize(self):
        """
            :description: Get lists with incorrect page_size.
            :resources: '/lists'
        """
        for _ in range(100):
            listId = self.FacesApi.createList(self.account_id, self.user_data, raiseError=True).json['list_id']
            self.listIds.append(listId)
            self.lists.append(listId)
        reply = self.FacesApi.getLists(pageSize=1000)
        self.validateJson(reply.json, SHEMA_GET_LISTS)
        self.assertGreaterEqual(reply.json['count'], 100)

    def test_get_lists_order_create_time(self):
        """
            :description: Get lists and check sorting by create_time in reply.
            :resources: '/lists'
        """
        reply = self.FacesApi.getLists(raiseError=True)
        listCreateTimeList = [list_['create_time'] for list_ in reply.json['lists']]
        self.assertEqual(listCreateTimeList, sorted(listCreateTimeList, reverse=True))

    def test_get_lists_create_time_sort_pages(self):
        """
            :description: Get lists and check sorting by create_time in reply.
            :resources: '/lists'
        """
        for _ in range(100):
            listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
            self.listIds.append(listId)
            self.lists.append(listId)
        reply = self.FacesApi.getLists(page=1, pageSize=50)
        self.validateJson(reply.json, SHEMA_GET_LISTS)
        listCreateTimeList = [list_['create_time'] for list_ in reply.json['lists']]
        reply = self.FacesApi.getLists(page=2, pageSize=50)
        self.validateJson(reply.json, SHEMA_GET_LISTS)
        listCreateTimeList.extend([list_['create_time'] for list_ in reply.json['lists']])
        self.assertEqual(listCreateTimeList, sorted(listCreateTimeList, reverse=True))

    def test_delete_lists(self):
        """
            :description: Delete lists.
            :resources: '/lists'
        """
        reply = self.FacesApi.deleteLists(listIds=self.listIds)
        self.assertEqual(reply.statusCode, 204)
        for listId in self.listIds:
            reply = self.FacesApi.getList(listId)
            self.assertErrorRestAnswer(reply, 404, Error.ListNotFound)

    def test_delete_lists_nonexists_listids(self):
        """
            :description: Delete non-existing lists.
            :resources: '/lists'
        """
        self.FacesApi.deleteLists(listIds=self.listIds)

        reply = self.FacesApi.deleteLists(self.listIds)
        self.assertErrorRestAnswer(reply, 400, Error.ListsNotFound)

    def test_delete_lists_nonexists_accountid(self):
        """
            :description: Delete lists with nonexists accountId.
            :resources: '/lists'
        """
        reply = self.FacesApi.deleteLists(listIds=self.listIds, accountId=str(uuid4()))
        self.assertErrorRestAnswer(reply, 400, Error.ListsNotFound)

    def test_delete_lists_badformat_accountid(self):
        """
            :description: Delete lists.
            :resources: '/lists'
        """
        badAccountId = 123
        reply = self.FacesApi.deleteLists(listIds=self.listIds, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_options_lists(self):
        """
            :description: Get lists with last link and unlink keys.
            :resources: '/lists'
        """
        numOfLists = 5
        lists = list()
        listIds, linkIds, unlinkIds = list(), list(), list()
        for numOfList in range(numOfLists):
            listId = self.FacesApi.createList(self.account_id, self.user_data, raiseError=True).json['list_id']
            self.lists.append(listId)
            self.faces.append(
                self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id'])
            self.FacesApi.link(listId, faceIds=[self.faces[-1]], action='attach', raiseError=True)
            self.FacesApi.link(listId, faceIds=[self.faces[-1]], action='detach', raiseError=True)
            self.FacesApi.link(listId, faceIds=[self.faces[-1]], action='attach', raiseError=True)
            linkKey = self.FacesApi.getAttributesFromList(listId, raiseError=True).json[0]['link_key']
            unlinkKey = self.FacesApi.getDeletionsFromList(listId, raiseError=True).json[0]['unlink_key']
            lists.append({'list_id': listId, 'link_key': linkKey, 'unlink_key': unlinkKey})

        reply = self.FacesApi.optionsLists([list_['list_id'] for list_ in lists])
        self.check_status_json_and_options_lists(reply, lists)

    def tests_options_list_without_link_key(self):
        """
            :description: Get list with last link and unlink keys | without link key.
            :resources: '/lists'
        """
        listId = self.FacesApi.createList(self.account_id, self.user_data, raiseError=True).json['list_id']
        self.lists.append(listId)
        self.faces.append(
            self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id'])
        self.FacesApi.link(listId, faceIds=[self.faces[-1]], action='attach', raiseError=True)
        self.FacesApi.link(listId, faceIds=[self.faces[-1]], action='detach', raiseError=True)
        unlinkKey = self.FacesApi.getDeletionsFromList(listId, raiseError=True).json[0]['unlink_key']

        reply = self.FacesApi.optionsLists([listId])
        self.check_status_json_and_options_lists(reply,
                                                 [{'list_id': listId, 'link_key': None, 'unlink_key': unlinkKey}])

    def tests_options_list_without_unlink_key(self):
        """
            :description: Get list with last link and unlink keys | without unlink key.
            :resources: '/lists'
        """
        listId = self.FacesApi.createList(self.account_id, self.user_data, raiseError=True).json['list_id']
        self.lists.append(listId)
        self.faces.append(
            self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id'])
        self.FacesApi.link(listId, faceIds=[self.faces[-1]], action='attach', raiseError=True)
        linkKey = self.FacesApi.getAttributesFromList(listId, raiseError=True).json[0]['link_key']

        reply = self.FacesApi.optionsLists([listId])
        self.check_status_json_and_options_lists(reply, [{'list_id': listId, 'link_key': linkKey, 'unlink_key': None}])

    def test_options_lists_empty_list(self):
        """
            :description: Get lists with link and unlink keys with no keys in list.
            :resources: '/lists'
        """
        listId = self.FacesApi.createList(self.account_id, self.user_data, raiseError=True).json['list_id']
        reply = self.FacesApi.optionsLists([listId])
        self.check_status_json_and_options_lists(reply, [{'list_id': listId, 'link_key': None, 'unlink_key': None}])

    def test_options_lists_bad_format_list_ids(self):
        """
            :description: Get lists with link and unlink keys with bad format list ids.
            :resources: '/lists'
        """
        badListIds = 123
        reply = self.FacesApi.optionsLists(listIds=badListIds)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['list_ids', str(badListIds) + ' is not of type \'array\''])

    def test_lists_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/lists'
        """
        self.methods_test('/lists', ['post', 'get', 'delete', 'options'])
