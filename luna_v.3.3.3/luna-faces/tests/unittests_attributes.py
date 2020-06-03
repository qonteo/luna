from tests.classes import TestBase
from uuid import uuid4
from luna_faces.crutches_on_wheels.errors.errors import Error


class TestAttributes(TestBase):
    """
    Test get attributes
    """

    def setUp(self):
        TestBase.setUp(self)
        self.facesListId = self.FacesApi.createList(self.account_id, self.user_data, raiseError=True).json['list_id']
        self.lists.append(self.facesListId)
        self.personsListId = self.FacesApi.createList(self.account_id, self.user_data, listType=1,
                                                      raiseError=True).json['list_id']
        self.lists.append(self.personsListId)

        self.attributesId = str(uuid4())
        faceId = self.FacesApi.createFace(self.account_id, attributesId=self.attributesId, raiseError=True).json[
            'face_id']
        self.faces.append(faceId)
        self.FacesApi.link(self.facesListId, [faceId], 'attach', raiseError=True)
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(personId)
        self.FacesApi.link(self.personsListId, personIds=[personId], action='attach', raiseError=True)
        self.FacesApi.linkFaceToPerson(faceId, personId, raiseError=True)

    def test_get_list_attributes(self):
        """
            :description: Get list's attributes.
            :resources: '/attributes'
        """
        for lunaList in [{"type": "persons", "list": self.personsListId}, {"type": "faces", "list": self.facesListId}]:
            with self.subTest(type=lunaList["type"]):
                reply = self.FacesApi.getAttributesIds(listId=lunaList["list"])
                self.assertEqual(reply.statusCode, 200)
                self.assertEqual(self.attributesId, reply.json['attributes'][0])

    def test_get_account_attributes(self):
        """
            :description: Get account's attributes.
            :resources: '/attributes'
        """
        accountId = str(uuid4())
        attrIds = []
        for _ in range(3):
            attributesId = str(uuid4())
            attrIds.append(attributesId)
            faceId = \
                self.FacesApi.createFace(accountId, attributesId=attributesId, raiseError=True).json['face_id']
            self.faces.append(faceId)
        reply = self.FacesApi.getAttributesIds(accountId=accountId)
        self.assertEqual(reply.statusCode, 200)
        self.assertListEqual(attrIds, reply.json['attributes'])

    def test_get_lists_time_sort(self):
        """
            :description: Get lists and check sorting by attributes_id by create_time of faces in recieved list.
            :resources: '/attributes'
        """
        attrIds = [self.attributesId]
        for _ in range(100):
            attributesId = str(uuid4())
            attrIds.append(attributesId)
            faceId = \
                self.FacesApi.createFace(self.account_id, attributesId=attributesId, raiseError=True).json['face_id']
            self.faces.append(faceId)
            self.FacesApi.link(self.facesListId, [faceId], 'attach', raiseError=True)

        reply = self.FacesApi.getAttributesIds(listId=self.facesListId)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(attrIds, reply.json['attributes'])

    def test_get_time_sort_pages(self):
        """
            :description: Get lists and check sorting by attributes_id by last_update_time of faces in recieved lists.
            :resources: '/attributes'
        """

        def attachAndDetachFaceToList(faceId):
            listId = self.FacesApi.createList(self.account_id, self.user_data, raiseError=True).json["list_id"]
            self.FacesApi.link(listId, [faceId], raiseError=True)
            self.FacesApi.link(listId, [faceId], "detach", raiseError=True)

        accountId = str(uuid4())
        attrIds = []

        def createFace():
            attributes = str(uuid4())
            face = self.FacesApi.createFace(accountId, attributesId=attributes, raiseError=True).json['face_id']

            return face, attributes

        testFceId, testAttributesId = createFace()

        for _ in range(99):
            faceId, attributesId = createFace()
            attrIds.append(attributesId)
            self.faces.append(faceId)

        attachAndDetachFaceToList(testFceId)
        attrIds.append(testAttributesId)
        self.faces.append(testFceId)

        reply = self.FacesApi.getAttributesIds(accountId=accountId, page=1, pageSize=50)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(attrIds[:50], reply.json['attributes'])
        reply = self.FacesApi.getAttributesIds(accountId=accountId, page=2, pageSize=50)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(attrIds[50:], reply.json['attributes'])

    def test_get_list_attributes_nonexists_listid(self):
        """
            :description: Get list's attributes with non-existing listId.
            :resources: '/attributes'
        """
        reply = self.FacesApi.getAttributesIds(str(uuid4()))
        self.assertErrorRestAnswer(reply, 400, Error.ListNotFound)

    def test_get_list_attributes_badformat_listid(self):
        """
            :description: Get list's attributes with bad format listId.
            :resources: '/attributes'
        """
        badListId = 123
        reply = self.FacesApi.getAttributesIds(badListId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['list_id', str(badListId) + ' is not of type \'string\''])

    def test_get_list_attributes_timelt(self):
        """
            :description: Get list's attributes with timeLt.
            :resources: '/attributes'
        """
        for lunaList in [{"type": "persons", "list": self.personsListId}, {"type": "faces", "list": self.facesListId}]:
            with self.subTest(type=lunaList["type"]):
                timeLt = self.getCurrentTimeStamp()
                reply = self.FacesApi.getAttributesIds(listId=lunaList["list"], timeLt=timeLt)
                self.assertEqual(reply.statusCode, 200)
                self.assertEqual(self.attributesId, reply.json['attributes'][0])

    def test_get_list_attributes_timegte(self):
        """
            :description: Get list's attributes with timeGte.
            :resources: '/attributes'
        """
        for lunaList in [{"type": "persons", "list": self.personsListId}, {"type": "faces", "list": self.facesListId}]:
            with self.subTest(type=lunaList["type"]):
                attributesId = str(uuid4())
                faceId = self.FacesApi.createFace(self.account_id, attributesId=attributesId, raiseError=True).json[
                    'face_id']
                self.faces.append(faceId)
                timeGte = self.getCurrentTimeStamp()
                self.FacesApi.link(self.facesListId, [faceId], 'attach', raiseError=True)

                reply = self.FacesApi.getAttributesIds(listId=self.facesListId, timeGte=timeGte)
                self.assertEqual(reply.statusCode, 200)
                self.assertEqual(reply.json['count'], 1)
                self.assertEqual(attributesId, reply.json['attributes'][0])

    def test_get_list_attributes_time(self):
        """
            :description: Get list's attributes with timeLt, timeGte.
            :resources: '/attributes'
        """
        for lunaList in [{"type": "persons", "list": self.personsListId}, {"type": "faces", "list": self.facesListId}]:
            with self.subTest(type=lunaList["type"]):
                listId = self.FacesApi.createList(self.account_id, self.user_data,
                                                  listType=1 if lunaList["type"] == "persons" else 0,
                                                  raiseError=True).json['list_id']
                self.lists.append(listId)
                attributesId = str(uuid4())
                faceId = self.FacesApi.createFace(self.account_id, attributesId=attributesId, raiseError=True).json[
                    'face_id']
                self.faces.append(faceId)
                timeGte = self.getCurrentTimeStamp()
                if lunaList["type"] == "persons":
                    personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
                    self.persons.append(personId)
                    self.FacesApi.link(listId, personIds=[personId], action='attach', raiseError=True)
                    self.FacesApi.linkFaceToPerson(faceId, personId, raiseError=True)
                else:
                    self.FacesApi.link(listId, [faceId], 'attach', raiseError=True)
                timeLt = self.getCurrentTimeStamp()

                reply = self.FacesApi.getAttributesIds(listId=listId, timeGte=timeGte, timeLt=timeLt)
                self.assertEqual(reply.statusCode, 200)
                self.assertEqual(attributesId, reply.json['attributes'][0])

    def test_get_list_attributes_time_format(self):
        """
            :description: Get list's attributes with timeLt in UTC and LOCAL formats.
            :resources: '/attributes'
        """
        for timeFormat in ('LOCAL', 'UTC'):
            with self.subTest(timeFormat=timeFormat):
                for lunaList in [{"type": "persons", "list": self.personsListId}, {"type": "faces", "list": self.facesListId}]:
                    with self.subTest(type=lunaList["type"]):
                        timeLt = self.getCurrentTimeStamp(timeFormat)
                        reply = self.FacesApi.getAttributesIds(listId=lunaList["list"], timeLt=timeLt)
                        self.assertEqual(reply.statusCode, 200)
                        self.assertEqual(self.attributesId, reply.json['attributes'][0])

    def test_get_attributes_wrong_time(self):
        """
            :description: Get list's attributes with wrong timeLt, timeGte.
            :resources: '/attributes'
        """
        timeGte = self.getCurrentTimeStamp()
        attributesId = str(uuid4())
        faceId = self.FacesApi.createFace(self.account_id, attributesId=attributesId, raiseError=True).json[
            'face_id']
        self.faces.append(faceId)
        self.FacesApi.link(self.facesListId, [faceId], 'attach', raiseError=True)
        timeLt = self.getCurrentTimeStamp()

        reply = self.FacesApi.getAttributesIds(accountId=self.account_id, timeGte=timeLt, timeLt=timeGte)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.json['count'], 0)

    def test_get_attributes_badformat_timelt(self):
        """
            :description: Get list's attributes with bad format timeLt.
            :resources: '/attributes''
        """
        badTimeLt = str(uuid4())
        reply = self.FacesApi.getAttributesIds(timeLt=badTimeLt)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['time__lt', str(badTimeLt) + ' is not of type \'string\''])

    def test_get_attributes_badformat_timegte(self):
        """
            :description: Get list's attributes with bad format timeGte.
            :resources: '/attributes'
        """
        badTimeGte = str(uuid4())
        reply = self.FacesApi.getAttributesIds(timeGte=badTimeGte)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['time__gte', str(badTimeGte) + ' is not of type \'string\''])

    def test_attributes_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/attributes'
        """
        self.methods_test('/attributes'.format(self.facesListId), ['get'])
