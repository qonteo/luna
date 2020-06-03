from tests.classes import TestBase
from uuid import uuid4
from luna_faces.crutches_on_wheels.errors.errors import Error

DEFAULT_FACES_COUNT = 3


class TestFaceLinker(TestBase):
    """
    Test Linker
    """

    def setUp(self):
        TestBase.setUp(self)
        self.personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(self.personId)

        self.faceIds = []
        for _ in range(DEFAULT_FACES_COUNT):
            faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json[
                'face_id']
            self.faceIds.append(faceId)
            self.faces.append(faceId)

        self.faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()),
                                               raiseError=True).json['face_id']
        self.faces.append(self.faceId)

    def test_link(self):
        """
            :description: Link face to person.
            :resources: '/facelinker'
        """
        reply = self.FacesApi.linkFaceToPerson(self.faceId, self.personId, 'attach')
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getPerson(self.personId)
        self.assertIn(self.faceId, reply.json['faces'])
        reply = self.FacesApi.getFace(self.faceId)
        self.assertEqual(self.personId, reply.json['person_id'])

    def test_link_nonexists_accountid(self):
        """
            :description: Link face to person with nonexists accountId.
            :resources: '/facelinker'
        """
        for action in ["attach", "detach"]:
            with self.subTest(action=action):
                reply = self.FacesApi.linkFaceToPerson(self.faceId, self.personId, action, accountId=str(uuid4()))
                self.assertErrorRestAnswer(reply, 400, Error.PersonNotFound)

    def test_link_nonexists_personid(self):
        """
            :description: Link face to person with nonexistent person id.
            :resources: '/facelinker'
        """
        for action in ["attach", "detach"]:
            with self.subTest(action=action):
                reply = self.FacesApi.linkFaceToPerson(self.faceId, str(uuid4()), action)
                self.assertErrorRestAnswer(reply, 400, Error.PersonNotFound)

    def test_link_badformat_accountid(self):
        """
            :description: Link face to person with bad format accountId.
            :resources: '/linker'
        """
        for action in ["attach", "detach"]:
            with self.subTest(action=action):
                badAccountId = 123
                reply = self.FacesApi.linkFaceToPerson(self.faceId, self.personId, action, accountId=badAccountId)
                self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                           msgFormat=['account_id', str(badAccountId) + ' is not of type \'string\''])

    def test_link_badformat_faceid(self):
        """
            :description: Link face to person with bad format listId.
            :resources: '/facelinker'
        """
        for action in ["attach", "detach"]:
            with self.subTest(action=action):
                badListId = 123
                reply = self.FacesApi.linkFaceToPerson(badListId, self.personId, action)
                self.assertEqual(reply.json["error_code"], Error.BadInputJson.errorCode)

    def test_link_nonexists_facesids(self):
        """
            :description: Link face to person with non-existing faceIds.
            :resources: '/facelinker'
        """
        for action in ["attach", "detach"]:
            with self.subTest(action=action):
                reply = self.FacesApi.linkFaceToPerson(str(uuid4()), self.personId, action)
                self.assertEqual(reply.statusCode, 400)
                self.assertIn('Face not found', reply.text)

    def test_unlink(self):
        """
            :description: Unlink face from person.
            :resources: '/facelinker'
        """
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(personId)
        faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
        self.faces.append(faceId)

        self.FacesApi.linkFaceToPerson(faceId, personId, action='attach', accountId=self.account_id, raiseError=True)

        reply = self.FacesApi.linkFaceToPerson(faceId, personId, action='detach', accountId=self.account_id)
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getPerson(personId)
        self.assertNotIn(faceId, reply.json['faces'])
        reply = self.FacesApi.getFace(faceId)
        self.assertEqual(None, reply.json['person_id'])

    def test_link_2_faces_to_person(self):
        """
            :description: Link 2 face to person.
            :resources: '/facelinker'
        """
        faceId1 = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
        self.faces.append(faceId1)
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(personId)
        self.FacesApi.linkFaceToPerson(faceId1, personId, 'attach', raiseError=True)
        faceId2 = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
        self.faces.append(faceId2)
        self.FacesApi.linkFaceToPerson(faceId2, personId, 'attach', raiseError=True)

        for face in [faceId1, faceId2]:
            reply = self.FacesApi.getPerson(personId)
            self.assertIn(face, reply.json['faces'])
            reply = self.FacesApi.getFace(face)
            self.assertEqual(personId, reply.json['person_id'])

    def test_link_already_linked_face_to_other_person(self):
        """
            :description: Link already_linked_face to person.
            :resources: '/facelinker'
        """

        personId1 = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(personId1)
        personId2 = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(personId2)
        faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
        self.faces.append(faceId)

        self.FacesApi.linkFaceToPerson(faceId, personId1, 'attach')
        reply = self.FacesApi.linkFaceToPerson(faceId, personId2, 'attach')
        self.assertErrorRestAnswer(reply, 409, Error.FaceAlreadyAttach)

    def test_link_face_to_person_in_list(self):
        """
            :description: Link person -> list; attribute -> face -> person. Check attribute in list attributes.
            :resources: '/facelinker'
        """
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(personId)

        attributesId = str(uuid4())
        faceId = self.FacesApi.createFace(self.account_id, attributesId=attributesId, raiseError=True).json['face_id']
        self.faces.append(faceId)

        listId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(listId)

        self.FacesApi.link(listId, personIds=[personId], raiseError=True)
        reply = self.FacesApi.linkFaceToPerson(faceId, personId, 'attach')
        self.assertEqual(reply.statusCode, 204)
        reply = self.FacesApi.getAttributesFromList(listId=listId, raiseError=True)
        self.assertIn(attributesId, reply.json[0]["attributes_id"])

    def test_unlink_face_from_another_person(self):
        """
            :description: Try to unlink person fromm face by wrong person id.
            :resources: '/facelinker'
        """
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        facePersonId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.extend((personId, facePersonId))

        faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
        self.faces.append(faceId)

        self.FacesApi.linkFaceToPerson(faceId, facePersonId, 'attach', raiseError=True)
        reply = self.FacesApi.linkFaceToPerson(faceId, personId, 'detach')
        self.assertErrorRestAnswer(reply, 400, Error.FaceWasNotAttachedToPerson)

        dbPersonId = self.FacesApi.getFace(faceId, self.account_id).json['person_id']
        self.assertEqual(facePersonId, dbPersonId, "Person was detached by wrong person id.")

    def test_linker_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/facelinker'
        """
        self.methods_test('/linker', ['patch'])
