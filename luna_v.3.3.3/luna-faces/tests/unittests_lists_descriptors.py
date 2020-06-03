import unittest

from tests.classes import TestBase
from uuid import uuid4
from luna_faces.crutches_on_wheels.errors.errors import Error
from tests.shemas import SCHEMA_GET_ATTRIBUTES_FROM_LIST, SCHEMA_GET_DELETIONS_FROM_LIST


class TestListsDescriptors(TestBase):
    """
    Test get attributes from list
    """

    def setUp(self):
        TestBase.setUp(self)
        self.facesListId = self.FacesApi.createList(self.account_id, self.user_data, raiseError=True).json['list_id']
        self.lists.append(self.facesListId)
        self.personsListId = self.FacesApi.createList(self.account_id, self.user_data, listType=1,
                                                      raiseError=True).json['list_id']
        self.lists.append(self.personsListId)

        self.attributesId = str(uuid4())
        self.faceId = self.FacesApi.createFace(self.account_id, attributesId=self.attributesId, raiseError=True).json[
            'face_id']
        self.faces.append(self.faceId)
        self.FacesApi.link(self.facesListId, [self.faceId], 'attach', raiseError=True)
        self.personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(self.personId)
        self.FacesApi.link(self.personsListId, personIds=[self.personId], action='attach', raiseError=True)
        self.FacesApi.linkFaceToPerson(self.faceId, self.personId, raiseError=True)

    def create_faces_and_link_to_list(self, linkToPerson=None):
        """
            :description: create faces and link to list
            :returns: linkKeyLt as linkKey of last face, linkKeyGte as linkKey of first face, attributes of all faces
        """
        numOfFaces = 5
        attributesIds = []
        listId = self.personsListId if linkToPerson is True else self.facesListId
        self.lists.append(listId)
        linkKeyGte = self.FacesApi.getAttributesFromList(listId=listId).json[0]['link_key']
        for _ in range(numOfFaces):
            attributesId = str(uuid4())
            attributesIds.append(attributesId)
            faceId = self.FacesApi.createFace(self.account_id, attributesId=attributesId, raiseError=True).json[
                'face_id']
            self.faces.append(faceId)
            self.FacesApi.link(listId=listId, faceIds=[faceId], action='attach', raiseError=True)
            if linkToPerson is True:
                self.FacesApi.linkFaceToPerson(faceId=faceId, personId=self.personId)
        linkKeyLt = self.FacesApi.getAttributesFromList(listId=listId).json[numOfFaces]['link_key']
        return linkKeyLt, linkKeyGte, attributesIds

    def check_status_code_and_json_link(self, reply):
        """
            :description: check reply status code and validate json
            :returns: none
        """
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_ATTRIBUTES_FROM_LIST)

    def check_status_code_and_json_unlink(self, reply):
        """
            :description: check reply status code and validate json
            :returns: none
        """
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_DELETIONS_FROM_LIST)

    def test_get_list_attributes(self):
        """
            :description: Get list's attributes.
            :resources: '/lists/{listId}/attributes'
        """
        for lunaList in [{"type": "persons", "list": self.personsListId}, {"type": "faces", "list": self.facesListId}]:
            with self.subTest(type=lunaList["type"]):
                reply = self.FacesApi.getAttributesFromList(listId=lunaList["list"])
                self.check_status_code_and_json_link(reply)
                self.assertEqual(self.attributesId, reply.json[0]['attributes_id'])

    def test_get_lists_attributes_sort(self):
        """
            :description: Get lists and check sorting by attributes_id.
            :resources: '/lists/{listId}/attributes'
        """
        attrIds = [self.attributesId]
        for _ in range(50):
            attributesId = str(uuid4())
            attrIds.append(attributesId)
            faceId = \
                self.FacesApi.createFace(self.account_id, attributesId=attributesId, raiseError=True).json['face_id']
            self.faces.append(faceId)
            self.FacesApi.link(self.facesListId, [faceId], 'attach', raiseError=True)

        reply = self.FacesApi.getAttributesFromList(listId=self.facesListId)
        replyAttrs = [attr['attributes_id'] for attr in reply.json]
        self.check_status_code_and_json_link(reply)
        self.assertEqual(attrIds, replyAttrs)

    def test_get_lists_attributes_limit(self):
        """
            :description: Get lists of attributes with limit.
            :resources: '/lists/{listId}/attributes'
        """
        attrIds = [self.attributesId]
        for _ in range(49):
            attributesId = str(uuid4())
            attrIds.append(attributesId)
            faceId = \
                self.FacesApi.createFace(self.account_id, attributesId=attributesId, raiseError=True).json['face_id']
            self.faces.append(faceId)
            self.FacesApi.link(self.facesListId, [faceId], 'attach', raiseError=True)

        reply = self.FacesApi.getAttributesFromList(listId=self.facesListId, limit=50)
        replyAttrs = [attr['attributes_id'] for attr in reply.json]
        self.check_status_code_and_json_link(reply)
        self.assertEqual(attrIds, replyAttrs)

    def test_get_list_attributes_nonexists_listid(self):
        """
            :description: Get list's attributes with non-existing listId.
            :resources: '/lists/{listId}/attributes'
        """
        reply = self.FacesApi.getAttributesFromList(str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.ListNotFound)

    def test_get_list_attributes_badformat_listid(self):
        """
            :description: Get list's attributes with bad format listId.
            :resources: '/lists/{listId}/attributes'
        """
        badListId = 123
        reply = self.FacesApi.getAttributesFromList(badListId)
        self.assertErrorRestAnswer(reply, 404, Error.PageNotFoundError)

    def test_get_list_attributes_face_to_list_link_key_lt(self):
        """
            :description: Get list's attributes with linkKeyLt after link and unlink face to/from list.
            :resources: '/lists/{listId}/attributes', '/lists/{listId}/deletions'
        """
        linkKeyLt, linkKeyGte, attributesIds = self.create_faces_and_link_to_list()

        with self.subTest(action='link'):
            reply = self.FacesApi.getAttributesFromList(listId=self.facesListId, linkKeyLt=linkKeyLt)
            self.check_status_code_and_json_link(reply)
            replyAttrIds = [attr['attributes_id'] for attr in reply.json]
            self.assertEqual([self.attributesId] + attributesIds[:-1], replyAttrIds)

        with self.subTest(action='unlink'):
            self.FacesApi.link(listId=self.facesListId, faceIds=[self.faceId], action='detach', raiseError=True)
            reply = self.FacesApi.getDeletionsFromList(listId=self.facesListId, linkKeyLt=linkKeyLt)
            self.check_status_code_and_json_unlink(reply)
            self.assertEqual(self.attributesId, reply.json[0]['attributes_id'])

    def test_get_list_attributes_face_to_list_link_key_gte(self):
        """
            :description: Get list's attributes with linkKeyGte after link and unlink face to/from list.
            :resources: '/lists/{listId}/attributes', '/lists/{listId}/deletions'
        """
        linkKeyLt, linkKeyGte, attributesIds = self.create_faces_and_link_to_list()

        with self.subTest(action='link'):
            reply = self.FacesApi.getAttributesFromList(listId=self.facesListId, linkKeyGte=linkKeyGte)
            self.check_status_code_and_json_link(reply)
            replyAttrIds = [attr['attributes_id'] for attr in reply.json]
            self.assertEqual([self.attributesId] + attributesIds, replyAttrIds)

        with self.subTest(action='unlink'):
            self.FacesApi.link(listId=self.facesListId, faceIds=[self.faceId], action='detach', raiseError=True)
            reply = self.FacesApi.getDeletionsFromList(listId=self.facesListId, linkKeyGte=linkKeyGte)
            self.check_status_code_and_json_unlink(reply)
            self.assertEqual(self.attributesId, reply.json[0]['attributes_id'])

    def test_get_list_attributes_face_to_list_link_key_gte_lt(self):
        """
            :description: Get list's attributes with linkKeyLt and linkKeyGte after link and unlink face to/from list.
            :resources: '/lists/{listId}/attributes', '/lists/{listId}/deletions'
        """
        linkKeyLt, linkKeyGte, attributesIds = self.create_faces_and_link_to_list()

        with self.subTest(action='link'):
            reply = self.FacesApi.getAttributesFromList(listId=self.facesListId, linkKeyLt=linkKeyLt,
                                                        linkKeyGte=linkKeyGte)
            self.check_status_code_and_json_link(reply)
            replyAttrIds = [attr['attributes_id'] for attr in reply.json]
            self.assertEqual([self.attributesId] + attributesIds[:-1], replyAttrIds)

        with self.subTest(action='unlink'):
            self.FacesApi.link(listId=self.facesListId, faceIds=[self.faceId], action='detach', raiseError=True)
            reply = self.FacesApi.getDeletionsFromList(listId=self.facesListId, linkKeyLt=linkKeyLt,
                                                       linkKeyGte=linkKeyGte)
            self.check_status_code_and_json_unlink(reply)
            self.assertEqual(self.attributesId, reply.json[0]['attributes_id'])

    def test_get_list_attributes_face_to_person_link_key_lt(self):
        """
            :description: Get list's attributes with linkKeyLt after link and unlink face to/from person.
            :resources: '/lists/{listId}/attributes', '/lists/{listId}/deletions'
        """
        linkKeyLt, linkKeyGte, attributesIds = self.create_faces_and_link_to_list(linkToPerson=True)

        with self.subTest(action='link'):
            reply = self.FacesApi.getAttributesFromList(listId=self.personsListId, linkKeyLt=linkKeyLt)
            self.check_status_code_and_json_link(reply)
            replyAttrIds = [attr['attributes_id'] for attr in reply.json]
            self.assertEqual([self.attributesId] + attributesIds[:-1], replyAttrIds)

        with self.subTest(action='unlink'):
            self.FacesApi.link(listId=self.personsListId, faceIds=[self.faceId], action='detach', raiseError=True)
            reply = self.FacesApi.getDeletionsFromList(listId=self.personsListId, linkKeyLt=linkKeyLt)
            self.check_status_code_and_json_unlink(reply)
            self.assertEqual(self.attributesId, reply.json[0]['attributes_id'])

    def test_get_list_attributes_person_to_list_link_key_gte(self):
        """
            :description: Get list's attributes with linkKeyGte after link and unlink face to/from person.
            :resources: '/lists/{listId}/attributes', '/lists/{listId}/deletions'
        """
        linkKeyLt, linkKeyGte, attributesIds = self.create_faces_and_link_to_list(linkToPerson=True)

        with self.subTest(action='link'):
            reply = self.FacesApi.getAttributesFromList(listId=self.personsListId, linkKeyGte=linkKeyGte)
            self.check_status_code_and_json_link(reply)
            replyAttrIds = [attr['attributes_id'] for attr in reply.json]
            self.assertEqual([self.attributesId] + attributesIds, replyAttrIds)

        with self.subTest(action='unlink'):
            self.FacesApi.link(listId=self.personsListId, faceIds=[self.faceId], action='detach', raiseError=True)
            reply = self.FacesApi.getDeletionsFromList(listId=self.personsListId, linkKeyGte=linkKeyGte)
            self.check_status_code_and_json_unlink(reply)
            self.assertEqual(self.attributesId, reply.json[0]['attributes_id'])

    def test_get_list_attributes_face_to_person_link_key_gte_lt(self):
        """
            :description: Get list's attributes with linkKeyLt and linkKeyGte after link and unlink face to/from person.
            :resources: '/lists/{listId}/attributes', '/lists/{listId}/deletions'
        """
        linkKeyLt, linkKeyGte, attributesIds = self.create_faces_and_link_to_list(linkToPerson=True)

        with self.subTest(action='link'):
            reply = self.FacesApi.getAttributesFromList(listId=self.personsListId, linkKeyLt=linkKeyLt,
                                                        linkKeyGte=linkKeyGte)
            self.check_status_code_and_json_link(reply)
            replyAttrIds = [attr['attributes_id'] for attr in reply.json]
            self.assertEqual([self.attributesId] + attributesIds[:-1], replyAttrIds)

        with self.subTest(action='unlink'):
            self.FacesApi.link(listId=self.personsListId, faceIds=[self.faceId], action='detach', raiseError=True)
            reply = self.FacesApi.getDeletionsFromList(listId=self.personsListId, linkKeyLt=linkKeyLt,
                                                       linkKeyGte=linkKeyGte)
            self.check_status_code_and_json_unlink(reply)
            self.assertEqual(self.attributesId, reply.json[0]['attributes_id'])

    def test_get_list_attributes_update_face(self):
        """
            :description: Get linker log by list id after update face with new attributes.
            :resources: '/lists/{listId}/attributes', '/lists/{listId}/deletions'
        """
        reply = self.FacesApi.getAttributesFromList(listId=self.facesListId)
        self.check_status_code_and_json_link(reply)
        self.assertEqual(self.attributesId, reply.json[0]['attributes_id'])
        linkKey = reply.json[0]['link_key']

        attributesId = str(uuid4())
        self.FacesApi.updateFace(faceId=self.faceId, attributesId=attributesId, accountId=self.account_id,
                                 raiseError=True)

        reply = self.FacesApi.getDeletionsFromList(listId=self.facesListId)
        self.check_status_code_and_json_unlink(reply)
        self.assertEqual(self.attributesId, reply.json[0]['attributes_id'])
        self.assertEqual(linkKey, reply.json[0]['link_key'])

    def test_get_list_attributes_delete_face(self):
        """
            :description: Get linker log by list id after delete face.
            :resources: '/lists/{listId}/attributes', '/lists/{listId}/deletions'
        """
        reply = self.FacesApi.getAttributesFromList(listId=self.facesListId)
        linkKey = reply.json[0]['link_key']
        self.FacesApi.deleteFace(faceId=self.faceId)

        reply = self.FacesApi.getDeletionsFromList(listId=self.facesListId)
        self.check_status_code_and_json_unlink(reply)
        self.assertEqual(self.attributesId, reply.json[0]['attributes_id'])
        self.assertEqual(linkKey, reply.json[0]['link_key'])

    def test_get_list_attributes_wrong_link_keys(self):
        """
            :description: Get list's attributes with wrong linkKeyLt, linkKeyGte.
            :resources: '/lists/{listId}/attributes'
        """
        reply = self.FacesApi.getAttributesFromList(listId=self.facesListId, linkKeyGte=1000,
                                                    linkKeyLt=0)
        self.check_status_code_and_json_link(reply)
        replyAttrIds = [attr['attributes_id'] for attr in reply.json]
        self.assertEqual(len(replyAttrIds), 0)

    def test_get_list_attributes_badformat_linkKeyLt(self):
        """
            :description: Get list's attributes with bad format linkKeyLt.
            :resources: '/lists/{listId}/attributes'
        """
        badlinkKeyLt = str(uuid4())
        reply = self.FacesApi.getAttributesFromList(listId=self.facesListId, linkKeyLt=badlinkKeyLt)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['link_key__lt', str(badlinkKeyLt) + ' is not of type \'string\''])

    def test_get_list_attributes_badformat_linkKeyGte(self):
        """
            :description: Get list's attributes with bad format linkKeyGte.
            :resources: '/lists/{listId}/attributes'
        """
        badlinkKeyGte = str(uuid4())
        reply = self.FacesApi.getAttributesFromList(listId=self.facesListId, linkKeyGte=badlinkKeyGte)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['link_key__gte', str(badlinkKeyGte) + ' is not of type \'string\''])

    def test_list_attributes_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/lists/{listId}/attributes'
        """
        self.methods_test('/lists/{}/attributes'.format(self.facesListId), ['get'])

    def test_clean_linker_log(self):
        """
            :description: clean log.
            :resources: '/linker/unlink_history'
        """
        self.FacesApi.deleteFace(self.faceId, raiseError=True)
        reply = self.FacesApi.getDeletionsFromList(listId=self.facesListId)
        self.assertNotEqual(len(reply.json), 0)

        reply = self.FacesApi.cleanLog()
        self.assertEqual(reply.statusCode, 204)

        reply = self.FacesApi.getDeletionsFromList(listId=self.facesListId)
        self.assertEqual(len(reply.json), 0)

    @unittest.skip("not stable (synchronization db time and server time)")
    def test_clean_linker_log_timelt(self):
        """
            :description: clean log with filter by timeLt.
            :resources: '/linker/unlink_history'
        """
        self.FacesApi.link(self.facesListId, faceIds=[self.faceId], action='detach', raiseError=True)
        timeLt = self.getCurrentTimeStamp()
        attributesId = str(uuid4())
        faceId = self.FacesApi.createFace(self.account_id, attributesId=attributesId, raiseError=True).json['face_id']
        self.faces.append(faceId)
        self.FacesApi.link(self.facesListId, faceIds=[faceId], action='attach', raiseError=True)
        self.FacesApi.link(self.facesListId, faceIds=[faceId], action='detach', raiseError=True)

        reply = self.FacesApi.cleanLog(timeLt=timeLt)
        self.assertEqual(reply.statusCode, 204)

        reply = self.FacesApi.getDeletionsFromList(listId=self.facesListId, raiseError=True)
        self.assertEqual(reply.json[0]['attributes_id'], attributesId)

    def test_clean_linker_log_timelt_bad_format(self):
        """
            :description: clean log with filter by timeLt with bad format timeLt.
            :resources: '/linker/unlink_history'
        """
        badTimeLt = str(uuid4())
        reply = self.FacesApi.cleanLog(timeLt=badTimeLt)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['time__lt', str(badTimeLt) + ' is not of type \'string\''])

    def test_get_list_attributes_face_linked_to_several_lists(self):
        """
            :description: Get link keys from two lists with one face after update face.
            :resources: '/lists/{listId}/attributes', '/lists/{listId}/deletions'
        """
        listIds = []
        for i in range(2):
            listId = self.FacesApi.createList(self.account_id, self.user_data, raiseError=True).json['list_id']
            self.lists.append(listId)
            listIds.append(listId)

            self.FacesApi.link(listId, [self.faceId], raiseError=True)
        self.FacesApi.updateFace(self.faceId, attributesId=self.attributesId)
        linkIds = [self.FacesApi.getAttributesFromList(listId, raiseError=True).json[0]['link_key']
                   for listId in listIds]
        self.assertNotEqual(*linkIds, "Link ids {} for different lists {} are the same!".format(linkIds, listIds))
