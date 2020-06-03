from uuid import uuid4
from tests.classes import TestBase
from luna_faces.crutches_on_wheels.errors.errors import Error
from tests.shemas import SHEMA_PERSON


PAGE_SIZE = 100


class TestPerson(TestBase):
    """
    Test Person
    """
    def setUp(self):
        TestBase.setUp(self)
        self.personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(self.personId)

    def test_head_person(self):
        """
            :description: Check person existence.
            :resources: '/persons/{person_id}'
        """
        reply = self.FacesApi.checkPerson(self.personId)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.body, b'')

    def test_head_person_nonexists_personid(self):
        """
            :description: Check person existence with nonexistent personId.
            :resources: '/persons/{person_id}'
        """
        reply = self.FacesApi.checkPerson(str(uuid4()))
        self.assertEqual(reply.statusCode, 404)
        self.assertEqual(reply.body, b'')

    def test_get_person(self):
        """
            :description: Get person.
            :resources: '/persons/{person_id}'
        """
        reply = self.FacesApi.getPerson(self.personId)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.json["person_id"], self.personId)
        self.validateJson(reply.json, SHEMA_PERSON)

    def test_get_person_nonexists_personid(self):
        """
            :description: Get person with nonexists personId.
            :resources: '/persons/{person_id}'
        """
        reply = self.FacesApi.getPerson(str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.PersonNotFound)

    def test_get_person_nonexists_accountid(self):
        """
            :description: Get person with non-existing accountId.
            :resources: '/persons/{person_id}'
        """
        reply = self.FacesApi.getPerson(self.personId, accountId=str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.PersonNotFound)

    def test_get_person_badformat_accountid(self):
        """
            :description: Get person with nonexists format accountId.
            :resources: '/persons/{person_id}'
        """
        badAccountId = 123
        reply = self.FacesApi.getPerson(self.personId, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_patch_person(self):
        """
            :description: Patch person.
            :resources: '/persons/{person_id}'
        """
        self.updateParams()
        externalId = 'test_external_id'
        reply = self.FacesApi.updatePerson(self.personId, userData=self.user_data, externalId=externalId)
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getPerson(self.personId)
        self.assertEqual(reply.json['account_id'], self.payload['account_id'])
        self.assertEqual(reply.json['user_data'], self.payload['user_data'])
        self.assertEqual(reply.json['external_id'], externalId)

    def test_patch_person_nonexists_personid(self):
        """
            :description: Patch person with nonexists personId.
            :resources: '/persons/{person_id}'
        """
        reply = self.FacesApi.updatePerson(str(uuid4()), self.user_data)
        self.assertErrorRestAnswer(reply, 404, Error.PersonNotFound)

    def test_patch_person_nonexists_accountid(self):
        """
            :description: Patch person with nonexists accountID.
            :resources: '/persons/{person_id}'
        """
        reply = self.FacesApi.updatePerson(self.personId, self.user_data, accountId=str(uuid4()))
        self.assertErrorRestAnswer(reply, 404, Error.PersonNotFound)

    def test_patch_person_badformat_accountid(self):
        """
            :description: Patch person with bad format accountID.
            :resources: '/persons/{person_id}'
        """
        badAccountId = 123
        reply = self.FacesApi.updatePerson(self.personId, self.user_data, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_patch_person_max_user_data(self):
        """
            :description: Patch person with max size of user_data.
            :resources: '/persons/{person_id}'
        """
        self.updateParams()
        reply = self.FacesApi.updatePerson(self.personId, userData='x'*128)
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getPerson(self.personId)
        self.assertEqual(reply.json['user_data'], 'x'*128)
        self.assertEqual(reply.json['account_id'], self.account_id)

    def test_patch_person_toolong_userdata(self):
        """
            :description: Patch person with user_data with size > max.
            :resources: '/persons/{person_id}'
        """
        reply = self.FacesApi.updatePerson(self.personId, userData='x'*129)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', '\''+'x'*129+'\''+' is too long'])

    def test_patch_person_toolong_external_id(self):
        """
            :description: Patch person with external_id with size > max.
            :resources: '/persons/{person_id}'
        """
        reply = self.FacesApi.updatePerson(self.personId, userData="123", externalId='x'*37)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['external_id', '\''+'x'*37+'\''+' is too long'])

    def test_delete_person(self):
        """
            :description: Delete person.
            :resources: '/persons/{person_id}'
        """
        reply = self.FacesApi.deletePerson(self.personId)
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getPerson(self.personId)
        self.assertErrorRestAnswer(reply, 404, Error.PersonNotFound)

    def test_delete_person_nonexists_accountid(self):
        """
            :description: Delete person with nonexists accountID.
            :resources: '/persons/{person_id}'
        """
        badAccountId = str(uuid4())
        reply = self.FacesApi.deletePerson(self.personId, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 404, Error.PersonNotFound)

    def test_delete_person_badformat_accountid(self):
        """
            :description: Delete person with bad format accountID.
            :resources: '/persons/{person_id}'
        """
        badAccountId = 123
        reply = self.FacesApi.deletePerson(self.personId, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_delete_person_nonexists(self):
        """
            :description: Delete non existing person.
            :resources: '/persons/{person_id}'
        """
        self.FacesApi.deletePerson(self.personId)
        reply = self.FacesApi.deletePerson(self.personId)
        self.assertErrorRestAnswer(reply, 404, Error.PersonNotFound)

    def test_person_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/persons/{person_id}'
        """
        self.methods_test('/persons/{}'.format(self.personId), ['get', 'patch', 'delete', 'head'])

