from tests.classes import TestBase
from tests.shemas import SCHEMA_REMOVING_FACES
import unittest
import uuid
from luna_faces.crutches_on_wheels.errors.errors import Error
import time


class TestGc(TestBase):
    """
    Tests not linked faces
    """

    @unittest.skip("touch all clients")
    def test_gc_all_free_faces(self):
        """
            :description: Remove not linked faces
            :resources: '/gc'
        """
        faceId = self.FacesApi.createFace(self.account_id, raiseError=True).json['face_id']
        self.faces.append(faceId)
        reply = self.FacesApi.removeNotLinkedFaces()
        self.validateJson(reply.json, SCHEMA_REMOVING_FACES)
        self.assertEqual(200, reply.statusCode)

    def test_gc_account_faces(self):
        """
            :description: Remove not linked faces of account
            :resources: '/gc'
        """
        faceId1 = self.FacesApi.createFace(self.account_id, attributesId=str(uuid.uuid4()), raiseError=True).json['face_id']
        self.faces.append(faceId1)
        faceId2 = self.FacesApi.createFace(str(uuid.uuid4()), attributesId=str(uuid.uuid4()), raiseError=True).json['face_id']
        self.faces.append(faceId2)
        reply = self.FacesApi.removeNotLinkedFaces(accountId=self.account_id)
        self.validateJson(reply.json, SCHEMA_REMOVING_FACES)
        self.assertEqual(200, reply.statusCode)
        reply = self.FacesApi.getFace(faceId1)
        self.assertErrorRestAnswer(reply, 404, Error.FaceNotFound)
        self.FacesApi.getFace(faceId2, raiseError=True)

    def test_gc_time(self):
        """
            :description: Remove not linked faces of account with filter by last update time
            :resources: '/gc'
        """
        faceId1 = self.FacesApi.createFace(self.account_id, attributesId=str(uuid.uuid4()), raiseError=True).json['face_id']
        self.faces.append(faceId1)
        time.sleep(0.01)

        faceId2 = self.FacesApi.createFace(self.account_id, attributesId=str(uuid.uuid4()), raiseError=True).json['face_id']
        self.faces.append(faceId2)
        timeLt = self.getCurrentTimeStamp()
        time.sleep(0.01)

        def attachAndDetachFaceToList(faceId):
            listId = self.FacesApi.createList(self.account_id, self.user_data, raiseError=True).json["list_id"]
            self.FacesApi.link(listId, [faceId], raiseError=True)
            self.FacesApi.link(listId, [faceId], "detach", raiseError=True)

        attachAndDetachFaceToList(faceId1)

        reply = self.FacesApi.removeNotLinkedFaces(accountId=self.account_id, timeLt=timeLt)
        self.validateJson(reply.json, SCHEMA_REMOVING_FACES)
        self.assertEqual(200, reply.statusCode)
        reply = self.FacesApi.getFace(faceId2)
        self.assertErrorRestAnswer(reply, 404, Error.FaceNotFound)
        self.FacesApi.getFace(faceId1, raiseError=True)

    def test_gc_limit(self):
        """
            :description: Remove not linked faces of account with limit
            :resources: '/gc'
        """
        faceId1 = self.FacesApi.createFace(self.account_id, attributesId=str(uuid.uuid4()),
                                           raiseError=True).json['face_id']
        self.faces.append(faceId1)
        faceId2 = self.FacesApi.createFace(str(uuid.uuid4()), attributesId=str(uuid.uuid4()),
                                           raiseError=True).json['face_id']
        self.faces.append(faceId2)
        reply = self.FacesApi.removeNotLinkedFaces(accountId=self.account_id, limit=1)
        self.validateJson(reply.json, SCHEMA_REMOVING_FACES)
        self.assertEqual(1, len(reply.json["face_ids"]))
        self.assertEqual(faceId1, reply.json["face_ids"][0])
        self.assertEqual(200, reply.statusCode)

    def test_gc_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/gc'
        """
        self.methods_test('/gc', ['patch'])
