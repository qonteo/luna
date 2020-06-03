from uuid import uuid4

from luna_faces.crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase
from tests.shemas import PERSON_ATTRIBUTES_LIST, PERSON_ATTRIBUTES


class TestPerson(TestBase):
    """
    Test person attributes
    """
    def createTestPerson(self) -> str:
        personId = self.createPerson()
        faceId = self.createFace(str(uuid4()))
        self.FacesApi.linkFaceToPerson(personId=personId, faceId=faceId, raiseError=True)
        return personId

    def test_get_person_attributes(self):
        """
            :description: Get person attributes.
            :resources: '/persons/{person_id}/attributes'
        """
        personId = self.createPerson()
        faceId1 = self.createFace(str(uuid4()))
        faceId2 = self.createFace(str(uuid4()))
        self.FacesApi.linkFaceToPerson(personId=personId, faceId=faceId1, raiseError=True)
        self.FacesApi.linkFaceToPerson(personId=personId, faceId=faceId2, raiseError=True)

        response = self.FacesApi.personAttributes(personId)
        self.validateJson(response.json, PERSON_ATTRIBUTES)
        self.assertEqual(len(response.json['attributes_ids']), 2)
        self.assertEqual(response.statusCode, 200)

    def test_get_person_attributes_not_found(self):
        """
            :description: Get not exist person attributes.
            :resources: '/faces/{person_id}/attributes'
        """
        response = self.FacesApi.personAttributes(str(uuid4()))
        self.assertErrorRestAnswer(response, 404, Error.PersonNotFound)

    def test_get_person_attributes_without_attributes(self):
        """
            :description: Get person attributes without attribute.
            :resources: '/persons/{person_id}/attributes'
        """
        personId = self.createPerson()
        response = self.FacesApi.personAttributes(personId)
        self.validateJson(response.json, PERSON_ATTRIBUTES)
        self.assertEqual(response.json['attributes_ids'], [])
        self.assertEqual(response.statusCode, 200)

    def test_get_person_attributes_for_account(self):
        """
            :description: Get person attributes for account.
            :resources: '/persons/{person_id}/attributes'
        """
        personId = self.createTestPerson()
        response = self.FacesApi.personAttributes(personId, accountId=self.account_id)
        self.validateJson(response.json, PERSON_ATTRIBUTES)
        self.assertEqual(len(response.json['attributes_ids']), 1)
        self.assertEqual(response.statusCode, 200)

    def test_get_person_attributes_for_wrong_account(self):
        """
            :description: Get person attributes with wrong account.
            :resources: '/persons/{person_id}/attributes'
        """
        personId = self.createTestPerson()
        response = self.FacesApi.personAttributes(personId, accountId=str(uuid4()))
        self.assertErrorRestAnswer(response, 404, Error.PersonNotFound)

    def test_get_person_without_attributes_with_account_id(self):
        """
            :description: Get not exist person attributes with account id.
            :resources: '/faces/{person_id}/attributes'
        """
        personId = self.createPerson()
        response = self.FacesApi.personAttributes(personId, accountId=self.account_id)
        self.assertEqual(response.statusCode, 200)
        self.assertEqual(len(response.json['attributes_ids']), 0)


class TestPersons(TestBase):
    """
    Test persons attributes
    """
    def createTwoTestPerson(self) -> tuple:
        personId1 = self.createPerson()
        faceId1 = self.createFace(str(uuid4()))
        self.FacesApi.linkFaceToPerson(personId=personId1, faceId=faceId1, raiseError=True)

        personId2 = self.createPerson()
        faceId2 = self.createFace(str(uuid4()))
        self.FacesApi.linkFaceToPerson(personId=personId2, faceId=faceId2, raiseError=True)

        return personId1, personId2

    def test_get_persons_attributes(self):
        """
            :description: Get person attributes.
            :resources: '/persons/attributes'
        """
        testPersonsIDs = self.createTwoTestPerson()

        response = self.FacesApi.personsAttributes(testPersonsIDs, raiseError=True)
        self.validateJson(response.json, PERSON_ATTRIBUTES_LIST)
        self.assertEqual(len(response.json), 2)
        self.assertEqual(response.statusCode, 200)

    def test_get_persons_attributes_with_non_exist_person_id(self):
        """
            :description: Get persons attributes with not exist person id.
            :resources: '/persons/attributes'
        """
        response = self.FacesApi.personsAttributes([str(uuid4()), str(uuid4())], raiseError=True)
        self.assertEqual(response.json, [])
        self.assertEqual(response.statusCode, 200)

    def test_get_persons_attributes_with_wrong_param(self):
        """
            :description: Get person attributes with wrong params.
            :resources: '/persons/attributes'
        """
        response = self.FacesApi.personsAttributes(['personId'])
        self.assertErrorRestAnswer(response, 400, Error.BadQueryParams, ['persons_ids'])

    def test_get_persons_attributes_for_account(self):
        """
            :description: Get persons attributes for account.
            :resources: '/persons/attributes'
        """
        testPersonsIDs = self.createTwoTestPerson()
        response = self.FacesApi.personsAttributes(testPersonsIDs, accountId=self.account_id, raiseError=True)
        self.validateJson(response.json, PERSON_ATTRIBUTES_LIST)
        self.assertEqual(len(response.json), 2)
        self.assertEqual(response.statusCode, 200)

    def test_get_persons_attributes_for_wrong_account(self):
        """
            :description: Get persons attributes with wrong account.
            :resources: '/persons/attributes'
        """
        testPersonsIDs = self.createTwoTestPerson()
        response = self.FacesApi.personsAttributes(testPersonsIDs, accountId=str(uuid4()), raiseError=True)
        self.validateJson(response.json, PERSON_ATTRIBUTES_LIST)
        self.assertEqual(response.json, [])
        self.assertEqual(response.statusCode, 200)
