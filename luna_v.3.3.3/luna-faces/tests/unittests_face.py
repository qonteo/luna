from uuid import uuid4
from datetime import timedelta
from tests.classes import TestBase
from luna_faces.crutches_on_wheels.errors.errors import Error
from tests.shemas import SHEMA_GET_FACE, SHEMA_CREATE_FACE
from dateutil import parser, tz


PAGE_SIZE = 100


class TestFace(TestBase):
    """
    Test Face
    """
    def setUp(self):
        TestBase.setUp(self)
        self.attributesId = str(uuid4())
        self.faceId = self.FacesApi.createFace(self.account_id,
                                               attributesId=self.attributesId, raiseError=True).json['face_id']
        self.faces.append(self.faceId)

    def test_head_face(self):
        """
            :description: Check face existence.
            :resources: '/faces/{face_id}'
        """
        reply = self.FacesApi.checkFace(self.faceId)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.body, b'')

    def test_head_face_nonexists_faceid(self):
        """
            :description: Check face existence.
            :resources: '/faces/{face_id}'
        """
        reply = self.FacesApi.checkFace(str(uuid4()))
        self.assertEqual(reply.statusCode, 404)
        self.assertEqual(reply.body, b'')

    def test_get_face(self):
        """
            :description: Get face.
            :resources: '/faces/{face_id}'
        """
        reply = self.FacesApi.getFace(self.faceId)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACE)

    def test_get_face_nonexists_faceid(self):
        """
            :description: Get face with nonexists faceId.
            :resources: '/faces/{face_id}'
        """
        reply = self.FacesApi.getFace(str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.FaceNotFound)

    def test_get_face_nonexists_accountid(self):
        """
            :description: Get face with non-existing accountId.
            :resources: '/faces/{face_id}'
        """
        reply = self.FacesApi.getFace(self.faceId, accountId=str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.FaceNotFound)

    def test_get_face_badformat_accountid(self):
        """
            :description: Get face with uncorrect faceId and uncorrect accountId.
            :resources: '/faces/{face_id}'
        """
        badAccountId = 123
        reply = self.FacesApi.getFace(self.faceId, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_patch_face(self):
        """
            :description: Patch face.
            :resources: '/faces/{face_id}'
        """
        self.updateParams()
        externalId = 'test_external_id'
        reply = self.FacesApi.updateFace(self.faceId, attributesId=self.attributes_id, eventId=self.event_id,
                                         userData=self.user_data, externalId=externalId)
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getFace(self.faceId)
        for param in self.payload:
            self.assertEqual(reply.json[param], self.payload[param])
        self.assertEqual(reply.json['external_id'], externalId)

    def test_patch_face_existing_attributesid(self):
        """
            :description: Patch face.
            :resources: '/faces/{face_id}'
        """
        reply = self.FacesApi.updateFace(self.faceId, attributesId=self.attributes_id, eventId=self.event_id,
                                         userData=self.user_data, raiseError=True)
        self.faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()),
                                               raiseError=True).json['face_id']
        self.faces.append(self.faceId)
        reply = self.FacesApi.updateFace(self.faceId, self.account_id, attributesId=self.attributes_id)
        self.assertErrorRestAnswer(reply, 409, Error.FaceWithAttributeOrIdAlreadyExist)

    def test_patch_face_nonexists_faceid(self):
        """
            :description: Patch face with nonexists faceId.
            :resources: '/faces/{face_id}'
        """
        reply = self.FacesApi.updateFace(str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.FaceNotFound)

    def test_patch_face_nonexists_accountid(self):
        """
            :description: Patch face with nonexists accountID.
            :resources: '/faces/{face_id}'
        """
        reply = self.FacesApi.updateFace(self.faceId, accountId=str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.FaceNotFound)

    def test_patch_face_badformat_accountid(self):
        """
            :description: Patch face with bad format accountID.
            :resources: '/faces/{face_id}'
        """
        badAccountId = 123
        reply = self.FacesApi.updateFace(self.faceId, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_patch_face_badformat_attributesid(self):
        """
            :description: Patch face with bad format attributesId.
            :resources: '/faces/{face_id}'
        """
        badAttributesId = 123
        reply = self.FacesApi.updateFace(self.faceId, attributesId=badAttributesId)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['attributes_id', str(badAttributesId)+' is not of type \'string\''])

    def test_patch_face_badformat_eventid(self):
        """
            :description: Patch face with bad format eventId.
            :resources: '/faces/{face_id}'
        """
        badEventId = 123
        reply = self.FacesApi.updateFace(self.faceId, eventId=badEventId)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['event_id', str(badEventId)+' is not of type \'string\''])

    def test_patch_face_max_user_data(self):
        """
            :description: Patch face with max size of user_data.
            :resources: '/faces/{face_id}'
        """
        self.updateParams()
        reply = self.FacesApi.updateFace(self.faceId, attributesId=self.attributes_id, eventId=self.event_id,
                                         userData='x'*128)
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getFace(self.faceId)
        self.assertEqual(reply.json['user_data'], 'x'*128)
        self.assertEqual(reply.json['account_id'], self.account_id)
        self.assertEqual(reply.json['attributes_id'], self.attributes_id)
        self.assertEqual(reply.json['event_id'], self.event_id)

    def test_patch_face_toolong_userdata(self):
        """
            :description: Patch face with user_data with size > max.
            :resources: '/faces/{face_id}'
        """
        reply = self.FacesApi.updateFace(self.faceId, userData='x'*129)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', '\''+'x'*129+'\''+' is too long'])

    def test_patch_face_toolong_extarnalid(self):
        """
            :description: Patch face with extarnal_id with size > max.
            :resources: '/faces/{face_id}'
        """
        reply = self.FacesApi.updateFace(self.faceId, externalId='x'*37)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['external_id', '\''+'x'*37+'\''+' is too long'])

    def test_patch_face_badformat_userdata(self):
        """
            :description: Patch face with bad format user data.
            :resources: '/faces/{face_id}'
        """
        badUserData = 123
        reply = self.FacesApi.updateFace(self.faceId, self.account_id, self.attributes_id, self.event_id, badUserData)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', str(badUserData) + ' is not of type \'string\''])

    def test_delete_face(self):
        """
            :description: Delete face.
            :resources: '/faces/{face_id}'
        """
        reply = self.FacesApi.deleteFace(self.faceId)
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getFace(self.faceId)
        self.assertErrorRestAnswer(reply, 404, Error.FaceNotFound)

    def test_delete_face_nonexists_accountid(self):
        """
            :description: Delete face with nonexists format accountID.
            :resources: '/faces/{face_id}'
        """
        nonExistsAccountId = str(uuid4())
        reply = self.FacesApi.deleteFace(self.faceId, accountId=nonExistsAccountId)
        self.assertErrorRestAnswer(reply, 404, Error.FaceNotFound)

    def test_delete_face_badformat_accountid(self):
        """
            :description: Delete face with bad format accountID.
            :resources: '/faces/{face_id}'
        """
        badAccountId = 123
        reply = self.FacesApi.deleteFace(self.faceId, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_delete_face_nonexists(self):
        """
            :description: Delete non existing face.
            :resources: '/faces/{face_id}'
        """
        self.FacesApi.deleteFace(self.faceId)
        reply = self.FacesApi.deleteFace(self.faceId)
        self.assertErrorRestAnswer(reply, 404, Error.FaceNotFound)

    def test_face_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/faces/{face_id}'
        """
        self.methods_test('/faces/{}'.format(self.faceId), ['get', 'patch', 'delete', 'put', 'head'])

    def test_put_face(self):
        """
            :description: Put face.
            :resources: '/faces/{faceId}'
        """
        faceId = str(uuid4())
        reply = self.FacesApi.putFace(faceId, accountId= self.account_id, attributesId= self.attributes_id,
                                      eventId= self.event_id, userData= self.user_data)
        self.faces.append(faceId)
        self.validateJson(reply.json, SHEMA_CREATE_FACE)

        createTime = self.FacesApi.getFace(faceId).json['create_time']
        delta_time = parser.parse(self.getCurrentTimeStamp()).replace(tzinfo=None) - \
                     parser.parse(createTime).astimezone(tz.tzlocal()).replace(tzinfo=None)
        self.assertTrue(delta_time < timedelta(seconds=2))

    def test_put_face_max_userdata(self):
        """
            :description: Put face with max size of user_data.
            :resources: '/faces/{faceId}'
        """
        faceId = str(uuid4())
        reply = self.FacesApi.putFace(faceId, accountId=self.account_id, attributesId=self.attributes_id,
                                      eventId=self.event_id, userData='x'*128)
        self.faces.append(faceId)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_CREATE_FACE)

        reply = self.FacesApi.getFace(reply.json['face_id'])
        self.assertEqual(reply.json["user_data"], 'x'*128)

    def test_put_face_excessive_userdata(self):
        """
            :description: Put face with user_data with size > max.
            :resources: '/faces/{faceId}'
        """
        faceId = str(uuid4())
        reply = self.FacesApi.putFace(faceId, accountId=self.account_id, attributesId=self.attributes_id,
                                      eventId=self.event_id, userData='x'*129)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', '\''+'x'*129+'\''+' is too long'])

    def test_put_face_badformat_userdata(self):
        """
            :description: Put face with bad format user data.
            :resources: '/faces/{faceId}'
        """
        faceId = str(uuid4())
        badUserData = 123
        reply = self.FacesApi.putFace(faceId, accountId=self.account_id, attributesId=self.attributes_id,
                                      eventId=self.event_id, userData=badUserData)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', str(badUserData) + ' is not of type \'string\''])

    def test_put_face_badformat_accountid(self):
        """
            :description: Put face with bad format accountId.
            :resources: '/faces/{faceId}'
        """
        faceId = str(uuid4())
        badAccountId = 123
        reply = self.FacesApi.putFace(faceId, accountId=badAccountId, attributesId=self.attributes_id,
                                      eventId=self.event_id, userData=self.user_data)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_put_face_badformat_attributesid(self):
        """
            :description: Put face with bad format attriburesId.
            :resources: '/faces/{faceId}'
        """
        faceId = str(uuid4())
        badAttributesId = 123
        reply = self.FacesApi.putFace(faceId, accountId=self.account_id,attributesId=badAttributesId,
                                      eventId=self.event_id, userData=self.user_data)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['attributes_id', str(badAttributesId)+' is not of type \'string\''])

    def test_put_face_badformat_eventid(self):
        """
            :description: Put face with bad format eventId.
            :resources: '/faces/{faceId}'
        """
        faceId = str(uuid4())
        badEventId = 123
        reply = self.FacesApi.putFace(faceId, accountId=self.account_id, attributesId=self.attributes_id,
                                      eventId=badEventId, userData=self.user_data)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['event_id', str(badEventId)+' is not of type \'string\''])

    def test_put_faces_attributes_alreadyexists(self):
        """
            :description: Put face with already exists attriburesId.
            :resources: '/faces/{faceId}'
        """
        faceId = str(uuid4())
        self.FacesApi.putFace(faceId, accountId=self.account_id, attributesId=self.attributes_id,
                              eventId=self.event_id, userData=self.user_data)
        self.faces.append(faceId)

        reply = self.FacesApi.putFace(str(uuid4()), accountId=self.account_id, attributesId=self.attributes_id,
                                      eventId=self.event_id, userData=self.user_data)
        self.assertErrorRestAnswer(reply, 409, Error.FaceWithAttributeOrIdAlreadyExist)

    def test__put__faces_faceid_alreadyexists(self):
        """
            :description: Put face with already exists attriburesId.
            :resources: '/faces/{faceId}'
        """
        faceId = str(uuid4())
        self.FacesApi.putFace(faceId, accountId=self.account_id, attributesId=self.attributes_id,
                              eventId=self.event_id, userData=self.user_data)
        self.faces.append(faceId)

        reply = self.FacesApi.putFace(faceId, accountId=self.account_id, attributesId=self.attributes_id,
                                      eventId=self.event_id, userData=self.user_data)
        self.assertErrorRestAnswer(reply, 409, Error.FaceWithAttributeOrIdAlreadyExist)
