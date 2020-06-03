from uuid import uuid4

from luna_faces.crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase
from tests.shemas import FACE_ATTRIBUTES_LIST, FACE_ATTRIBUTES


class TestFace(TestBase):
    """
    Test face attributes
    """
    def test_get_face_attributes(self):
        """
            :description: Get face attributes.
            :resources: '/faces/{face_id}/attributes'
        """
        faceId = self.createFace(str(uuid4()))
        response = self.FacesApi.faceAttributes(faceId, raiseError=True)
        self.validateJson(response.json, FACE_ATTRIBUTES)
        self.assertEqual(response.statusCode, 200)

    def test_get_face_attributes_not_found(self):
        """
            :description: Get not exist face attributes.
            :resources: '/faces/{face_id}/attributes'
        """
        response = self.FacesApi.faceAttributes(str(uuid4()))
        self.assertErrorRestAnswer(response, 404, Error.FaceNotFound)

    def test_get_face_attributes_is_none(self):
        """
            :description: Get face attributes with attribute is none.
            :resources: '/faces/{face_id}/attributes'
        """
        faceId = self.createFace(None)
        response = self.FacesApi.faceAttributes(faceId, raiseError=True)
        self.validateJson(response.json, FACE_ATTRIBUTES)
        self.assertEqual(response.statusCode, 200)

    def test_get_face_attributes_for_account(self):
        """
            :description: Get face attributes for account id.
            :resources: '/faces/{face_id}/attributes'
        """
        faceId = self.createFace(str(uuid4()))
        response = self.FacesApi.faceAttributes(faceId, accountId=self.account_id, raiseError=True)
        self.validateJson(response.json, FACE_ATTRIBUTES)
        self.assertEqual(response.statusCode, 200)

    def test_get_face_attributes_for_wrong_account(self):
        """
            :description: Get face attributes for wrong account id.
            :resources: '/faces/{face_id}/attributes'
        """
        faceId = self.createFace(str(uuid4()))
        response = self.FacesApi.faceAttributes(faceId, accountId=str(uuid4()))
        self.assertErrorRestAnswer(response, 404, Error.FaceNotFound)


class TestFacesAttributes(TestBase):
    """
    Test faces attributes
    """
    def test_get_faces_attributes(self):
        """
            :description: Get face attributes.
            :resources: '/faces/attributes'
        """
        facesIds = [self.createFace(str(uuid4())) for _ in range(3)]
        response = self.FacesApi.facesAttributes(facesIds, raiseError=True)
        self.validateJson(response.json, FACE_ATTRIBUTES_LIST)
        self.assertEqual(len(response.json), 3)
        self.assertEqual(response.statusCode, 200)

    def test_get_faces_attributes_with_non_exist_face_id(self):
        """
            :description: Get faces attributes with not exist face id.
            :resources: '/faces/attributes'
        """
        response = self.FacesApi.facesAttributes([str(uuid4()), str(uuid4())], raiseError=True)
        self.assertEqual(response.json, [])
        self.assertEqual(response.statusCode, 200)

    def test_get_faces_attributes_with_wrong_param(self):
        """
            :description: Get face attributes with wrong params.
            :resources: '/faces/attributes'
        """
        response = self.FacesApi.facesAttributes(['facesIds'])
        self.assertErrorRestAnswer(response, 400, Error.BadQueryParams, ['faces_ids'])

    def test_get_faces_attributes_for_account(self):
        """
            :description: Get faces attributes for account id.
            :resources: '/faces/attributes'
        """
        facesIds = [self.createFace(str(uuid4())) for _ in range(3)]
        response = self.FacesApi.facesAttributes(facesIds, accountId=self.account_id, raiseError=False)
        self.validateJson(response.json, FACE_ATTRIBUTES_LIST)
        self.assertEqual(len(response.json), 3)
        self.assertEqual(response.statusCode, 200)

    def test_get_faces_attributes_for_wrong_account(self):
        """
            :description: Get faces attributes for wrong account id.
            :resources: '/faces/attributes'
        """
        facesIds = [self.createFace(str(uuid4())) for _ in range(3)]
        response = self.FacesApi.facesAttributes(facesIds, accountId=str(uuid4()))
        self.assertEqual(response.json, [])
        self.assertEqual(response.statusCode, 200)
