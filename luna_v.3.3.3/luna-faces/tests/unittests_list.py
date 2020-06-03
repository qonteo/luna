import unittest
from uuid import uuid4
from tests.classes import TestBase
from luna_faces.crutches_on_wheels.errors.errors import Error
from tests.shemas import SHEMA_GET_LIST
from dateutil import parser

PAGE_SIZE = 100


class TestList(TestBase):
    """
    Test List
    """

    def setUp(self):
        TestBase.setUp(self)
        self.listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(self.listId)

    def test_head_list(self):
        """
            :description: Check list existence.
            :resources: '/lists/{list_id}'
        """
        reply = self.FacesApi.checkList(self.listId)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.body, b'')

    def test_head_list_nonexists_listid(self):
        """
            :description: Check list existence with nonexistent listId.
            :resources: '/lists/{list_id}'
        """
        reply = self.FacesApi.checkList(str(uuid4()))
        self.assertEqual(reply.statusCode, 404)
        self.assertEqual(reply.body, b'')

    def test_get_list(self):
        """
            :description: Get list.
            :resources: '/lists/{list_id}'
        """
        reply = self.FacesApi.getList(self.listId)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_LIST)

    def test_get_list_last_update_time_after_link_face(self):
        """
            :description: Get list with correct last update time after link face to list
            :resources: '/lists/{list_id}'
        """
        listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        updateListTime = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.lists.append(listId)
        faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
        self.faces.append(faceId)
        self.FacesApi.link(listId, [faceId])
        updateListTimeAfterLink = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.assertTrue(updateListTime < updateListTimeAfterLink,
                        "last update time didn't change after link face to list")

    def test_get_list_last_update_time_after_link_person(self):
        """
            :description: Get list with correct last update time after link person to list
            :resources: '/lists/{list_id}'
        """
        listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(listId)
        updateListTime = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(personId)
        self.FacesApi.link(listId=listId, action="attach", personIds=[personId],raiseError=True)
        updateListTimeAfterLink = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.assertTrue(updateListTime < updateListTimeAfterLink,
                        "last update time didn't change after link person to list")

    def test_get_list_last_update_time_after_unlink_person(self):
        """
            :description: Get list with correct last update time after unlink person from list
            :resources: '/lists/{list_id}'
        """
        listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(listId)
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(personId)
        self.FacesApi.link(listId=listId, action="attach", personIds=[personId], raiseError=True)
        updateListTime = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.FacesApi.link(listId=listId, action="detach", personIds=[personId], raiseError=True)
        updateListTimeAfterLink = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.assertTrue(updateListTime < updateListTimeAfterLink,
                        "last update time didn't change after unlink person to list")

    def test_get_list_last_update_time_after_unlink_face_on_person(self):
        """
            :description: Get list with correct last update time after unlink face from person
            :resources: '/lists/{list_id}'
        """
        listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(listId)
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
        self.FacesApi.linkFaceToPerson(faceId=faceId, personId=personId, action="attach")
        self.persons.append(personId)
        self.FacesApi.link(listId=listId, action="attach", personIds=[personId])
        updateListTime = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.FacesApi.linkFaceToPerson(faceId=faceId, personId=personId, action="detach")
        updateListTimeAfterUnLink = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.assertTrue(updateListTime < updateListTimeAfterUnLink,
                        "last update time didn't change after unlink face to person to list")

    def test_get_list_last_update_time_after_link_face_on_person(self):
        """
            :description: Get list with correct last update time after link face to person
            :resources: '/lists/{list_id}'
        """
        listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(listId)
        personId = self.FacesApi.createPerson(self.account_id,raiseError=True).json['person_id']
        faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
        self.persons.append(personId)
        self.FacesApi.link(listId=listId, action="attach", personIds=[personId])
        updateListTime = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.FacesApi.linkFaceToPerson(faceId=faceId, personId=personId, action="attach")
        updateListTimeAfterLink = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.assertTrue(updateListTime < updateListTimeAfterLink,
                        "last update time didn't change after unlink face to person to list")

    def test_get_list_last_update_time_after_delete_face_on_person(self):
        """
            :description: Get list with correct last update time after delete face from person
            :resources: '/lists/{list_id}'
        """
        listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(listId)
        personId = self.FacesApi.createPerson(self.account_id,raiseError=True).json['person_id']
        faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json[
            'face_id']
        self.faces.append(faceId)
        self.FacesApi.linkFaceToPerson(faceId=faceId, personId=personId, action="attach")
        self.persons.append(personId)
        self.FacesApi.link(listId=listId, action="attach", personIds=[personId])
        updateListTime = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.FacesApi.deleteFace(faceId=faceId, accountId=self.account_id)
        updateListTimeAfterDelete = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.assertTrue(updateListTime < updateListTimeAfterDelete,
                        "last update time didn't change after delete face on person to list")

    def test_list_last_update_time_after_add_1_person_to_2_lists_and_then_remove_from_1(self):
        """
            :description: Get list with correct last update time after add one person to single lists and then remove from one
            :resources: '/lists/{list_id}'
        """
        listId1 = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        listId2 = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append([listId1, listId2])
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.FacesApi.link(listId=listId1, action="attach", personIds=[personId], raiseError=True)
        updateListTime = parser.parse(self.FacesApi.getList(listId1).json['last_update_time']).timestamp()
        self.FacesApi.link(listId=listId2, action="attach", personIds=[personId], raiseError=True)
        self.FacesApi.link(listId=listId2, action="detach", personIds=[personId], raiseError=True)
        updateListTimeAfterLink = parser.parse(self.FacesApi.getList(listId1).json['last_update_time']).timestamp()
        self.assertTrue(updateListTime == updateListTimeAfterLink,
                        "last update time change after unlink person another list ")

    def test_get_list_last_update_time_after_unlink_face_from_person(self):
        """
            :description: Get list with correct last update time after unlink face from person
            :resources: '/lists/{list_id}'
        """
        listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(listId)
        faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
        self.FacesApi.link(listId, [faceId])
        self.faces.append(faceId)
        updateListTime = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.FacesApi.link(listId, [faceId], action='detach')
        updateListTimeAfterULink = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.assertTrue(updateListTime < updateListTimeAfterULink,
                        "last update time didn't change after link face to list")

    def test_get_list_last_update_time_after_delete_face(self):
        """
            :description: Get list with correct last update time after deleting faces
            :resources: '/lists/{list_id}'
        """
        listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(listId)
        faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
        self.FacesApi.link(listId, [faceId])
        self.faces.append(faceId)
        updateListTime = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.FacesApi.deleteFace(faceId=faceId, accountId=self.account_id)
        updateListTimeAfterDelete = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.assertTrue(updateListTime < updateListTimeAfterDelete, "last update time didn't change after delete face")

    def test_get_list_last_update_time_after_changer_person_user_data(self):
        """
            :description: Get list with correct last update time after change user data
            :resources: '/lists/{list_id}'
        """
        listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(listId)
        personId = self.FacesApi.createPerson(self.account_id,raiseError=True).json['person_id']
        self.persons.append(personId)
        faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
        self.faces.append(faceId)
        self.FacesApi.linkFaceToPerson(faceId, personId)
        self.FacesApi.link(listId=listId, action="attach", personIds=[personId])
        updateListTime = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.FacesApi.updatePerson(personId, userData=self.user_data)
        updateListTimeAfterLink = parser.parse(self.FacesApi.getList(listId).json['last_update_time']).timestamp()
        self.assertTrue(updateListTime == updateListTimeAfterLink,
                        "last update time changed after person's user data has been changed")

    def test_get_list_with_page_size(self):
        """
            :description: Get list with page size.
            :resources: '/lists/{list_id}'
        """
        listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(listId)
        faces = [self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
                 for _ in range(2)]
        self.faces.extend(faces)
        self.FacesApi.link(listId, faces, raiseError=True)
        cases = {0: [], 1: [faces[1]], 2: list(reversed(faces))}
        for pageSize in cases:
            with self.subTest(pageSize=pageSize):
                reply = self.FacesApi.getList(listId, page=1, pageSize=pageSize)
                self.assertEqual(reply.statusCode, 200)
                self.validateJson(reply.json, SHEMA_GET_LIST)
                self.assertListEqual(cases[pageSize], [face["face_id"] for face in reply.json['faces']])

    def test_get_list_nonexists_listid(self):
        """
            :description: Get list with nonexists listId.
            :resources: '/lists/{list_id}'
        """
        reply = self.FacesApi.getList(str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.ListNotFound)

    def test_get_list_nonexists_accountid(self):
        """
            :description: Get list with non-existing accountId.
            :resources: '/lists/{list_id}'
        """
        reply = self.FacesApi.getList(self.listId, accountId=str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.ListNotFound)

    def test_get_list_badformat_accountid(self):
        """
            :description: Get list with nonexists format accountId.
            :resources: '/lists/{list_id}'
        """
        badAccountId = 123
        reply = self.FacesApi.getList(self.listId, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId) + ' is not of type \'string\''])

    def test_patch_list(self):
        """
            :description: Patch list.
            :resources: '/lists/{list_id}'
        """
        self.updateParams()
        reply = self.FacesApi.updateListUserData(self.listId, userData=self.user_data)
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getList(self.listId)
        self.assertEqual(reply.json['account_id'], self.payload['account_id'])
        self.assertEqual(reply.json['user_data'], self.payload['user_data'])

    def test_patch_list_nonexists_listid(self):
        """
            :description: Patch list with nonexists listId.
            :resources: '/lists/{list_id}'
        """
        reply = self.FacesApi.updateListUserData(str(uuid4()), self.user_data)
        self.assertErrorRestAnswer(reply, 404, Error.ListNotFound)

    def test_patch_list_nonexists_accountid(self):
        """
            :description: Patch list with nonexists accountID.
            :resources: '/lists/{list_id}'
        """
        reply = self.FacesApi.updateListUserData(self.listId, self.user_data, accountId=str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.ListNotFound)

    def test_patch_list_badformat_accountid(self):
        """
            :description: Patch list with bad format accountID.
            :resources: '/lists/{list_id}'
        """
        badAccountId = 123
        reply = self.FacesApi.updateListUserData(self.listId, self.user_data, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId) + ' is not of type \'string\''])

    def test_patch_list_max_user_data(self):
        """
            :description: Patch list with max size of user_data.
            :resources: '/lists/{list_id}'
        """
        self.updateParams()
        reply = self.FacesApi.updateListUserData(self.listId, userData='x' * 128)
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getList(self.listId)
        self.assertEqual(reply.json['user_data'], 'x' * 128)
        self.assertEqual(reply.json['account_id'], self.account_id)

    def test_patch_list_toolong_userdata(self):
        """
            :description: Patch list with user_data with size > max.
            :resources: '/lists/{list_id}'
        """
        reply = self.FacesApi.updateListUserData(self.listId, userData='x' * 129)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', '\'' + 'x' * 129 + '\'' + ' is too long'])

    def test_create_list_badformat_userdata(self):
        """
            :description: Patch list with bad format user data.
            :resources: '/lists/{list_id}'
        """
        badUserData = 123
        reply = self.FacesApi.createList(self.account_id, badUserData)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', str(badUserData) + ' is not of type \'string\''])

    def test_delete_list(self):
        """
            :description: Delete list.
            :resources: '/lists/{list_id}'
        """
        reply = self.FacesApi.deleteList(self.listId)
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getList(self.listId)
        self.assertErrorRestAnswer(reply, 404, Error.ListNotFound)

    def test_delete_list_nonexists_accountid(self):
        """
            :description: Delete list with nonexists accountID.
            :resources: '/lists/{list_id}'
        """
        badAccountId = str(uuid4())
        reply = self.FacesApi.deleteList(self.listId, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 404, Error.ListNotFound)

    def test_delete_list_badformat_accountid(self):
        """
            :description: Delete list with bad format accountID.
            :resources: '/lists/{list_id}'
        """
        badAccountId = 123
        reply = self.FacesApi.deleteList(self.listId, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId) + ' is not of type \'string\''])

    def test_delete_list_nonexists(self):
        """
            :description: Delete non existing list.
            :resources: '/lists/{list_id}'
        """
        self.FacesApi.deleteList(self.listId)
        reply = self.FacesApi.deleteList(self.listId)
        self.assertErrorRestAnswer(reply, 404, Error.ListNotFound)

    def test_list_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/lists/{list_id}'
        """
        self.methods_test('/lists/{}'.format(self.listId), ['get', 'patch', 'delete', 'head'])
