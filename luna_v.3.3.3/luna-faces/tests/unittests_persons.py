from tests.classes import TestBase
from uuid import uuid4
from luna_faces.crutches_on_wheels.errors.errors import Error
from tests.shemas import SHEMA_CREATE_PERSON, SCHEMA_GET_PERSONS
from time import sleep

DEFAULT_PERSONS_COUNT = 3
PAGE_SIZE = 100


class TestPersons(TestBase):
    """
    Test Persons
    """

    def setUp(self):
        TestBase.setUp(self)
        self.personIds = []
        for _ in range(DEFAULT_PERSONS_COUNT):
            personId = self.FacesApi.createPerson(self.account_id, self.user_data, raiseError=True).json['person_id']
            self.personIds.append(personId)
            self.persons.append(personId)

    def test_create_person(self):
        """
            :description: Create person.
            :resources: '/persons'
        """
        reply = self.FacesApi.createPerson(self.account_id, self.user_data)
        self.persons.append(reply.json['person_id'])
        self.assertEqual(reply.statusCode, 201)
        self.validateJson(reply.json, SHEMA_CREATE_PERSON)

    def test_create_person_max_userdata(self):
        """
            :description: Create person with max size of user_data.
            :resources: '/persons'
        """
        reply = self.FacesApi.createPerson(self.account_id, 'x' * 128)
        self.persons.append(reply.json['person_id'])
        self.assertEqual(reply.statusCode, 201)
        self.validateJson(reply.json, SHEMA_CREATE_PERSON)

    def test_create_face_badformat_externalid(self):
        """
            :description: Create person with bad format external id.
            :resources: '/faces'
        """
        badformatExternalId = 123
        reply = self.FacesApi.createPerson(self.account_id, externalId=badformatExternalId)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['external_id', str(badformatExternalId)+' is not of type \'string\''])

    def test_create_list_excessive_userdata(self):
        """
            :description: Create list with user_data with size > max.
            :resources: '/persons'
        """
        reply = self.FacesApi.createPerson(self.account_id, 'x' * 129)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', '\'' + 'x' * 129 + '\'' + ' is too long'])

    def test_create_list_excessive_external_id(self):
        """
            :description: Create list with external_id with size > max.
            :resources: '/persons'
        """
        reply = self.FacesApi.createPerson(self.account_id, 'x' * 37)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['external_id', '\'' + 'x' * 37 + '\'' + ' is too long'])

    def test_create_list_badformat_userdata(self):
        """
            :description: Create list with bad format user data.
            :resources: '/persons'
        """
        badUserData = 123
        reply = self.FacesApi.createPerson(self.account_id, badUserData)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', str(badUserData) + ' is not of type \'string\''])

    def test_create_list_badformat_accountid(self):
        """
            :description: Create list with bad format accountId.
            :resources: '/persons'
        """
        badAccountId = 123
        reply = self.FacesApi.createPerson(badAccountId, self.user_data)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['account_id', str(badAccountId) + ' is not of type \'string\''])

    def test_get_persons(self):
        """
            :description: Get persons.
            :resources: '/persons'
        """
        reply = self.FacesApi.getPersons(self.user_data)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)

    def test_get_persons_partuserdata(self):
        """
            :description: Get persons.
            :resources: '/persons'
        """
        reply = self.FacesApi.getPersons(self.user_data[:len(self.user_data) // 2])
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)

    def test_get_persons_accountid(self):
        """
            :description: Get persons with accountID.
            :resources: '/persons'
        """
        self.personId = self.FacesApi.createPerson(str(uuid4()), self.user_data).json['person_id']
        self.persons.append(self.personId)
        reply = self.FacesApi.getPersons(self.user_data, self.account_id)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        replyPersonsIds = [personId['person_id'] for personId in reply.json['persons']]
        for personId in self.personIds:
            self.assertIn(personId, replyPersonsIds)
        self.assertNotIn(self.personId, replyPersonsIds)

    def test_get_persons_nonexists_accountid(self):
        """
            :description: Get persons with nonexists accountID.
            :resources: '/persons'
        """
        reply = self.FacesApi.getPersons(self.user_data, accountId=str(uuid4()))
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        self.assertEqual(reply.json['count'], 0)

    def test_get_persons_badformat_accountid(self):
        """
            :description: Get persons with bad format accountID.
            :resources: '/persons'
        """
        badAccountId = 123
        reply = self.FacesApi.getPersons(self.user_data, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId) + ' is not of type \'string\''])

    def test_get_persons_page_pagesize(self):
        """
            :description: Get persons with max page_size.
            :resources: '/persons'
        """
        reply = self.FacesApi.getPersons(self.user_data, page=1, pageSize=100)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        self.assertEqual(reply.statusCode, 200)
        self.assertGreaterEqual(reply.json['count'], DEFAULT_PERSONS_COUNT)

    def test_get_persons_page(self):
        """
            :description: Get persons with page=-1.
            :resources: '/persons'
        """
        reply = self.FacesApi.getPersons(self.user_data, page=-1, pageSize=100)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        self.assertGreaterEqual(reply.json['count'], DEFAULT_PERSONS_COUNT)

    def test_get_persons_bad_pagesize(self):
        """
            :description: Get persons with incorrect page_size.
            :resources: '/persons'
        """
        for _ in range(100):
            personId = self.FacesApi.createPerson(self.account_id, self.user_data, raiseError=True).json['person_id']
            self.personIds.append(personId)
            self.persons.append(personId)
        reply = self.FacesApi.getPersons(self.user_data, pageSize=1000)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        self.assertGreaterEqual(reply.json['count'], 100)

    def test_get_persons_time_sort(self):
        """
            :description: Get persons and check sorting by create_time in recieved list.
            :resources: '/persons'
        """
        for _ in range(100):
            personId = self.FacesApi.createPerson(self.account_id, self.user_data, raiseError=True).json['person_id']
            self.personIds.append(personId)
            self.persons.append(personId)
        reply = self.FacesApi.getPersons(self.user_data, pageSize=100)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        personCreateTimeList = [person['create_time'] for person in reply.json['persons']]
        self.assertEqual(personCreateTimeList, sorted(personCreateTimeList, reverse=True))

    def test_get_persons_time_sort_pages(self):
        """
            :description: Get persons and check sorting by create_time in recieved lists.
            :resources: '/persons'
        """
        for _ in range(100):
            personId = self.FacesApi.createPerson(self.account_id, self.user_data, raiseError=True).json[
                'person_id']
            self.personIds.append(personId)
            self.persons.append(personId)
        reply = self.FacesApi.getPersons(self.user_data, page=1, pageSize=50)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        personCreateTimeList = [person['create_time'] for person in reply.json['persons']]
        self.assertEqual(personCreateTimeList, sorted(personCreateTimeList, reverse=True))
        reply = self.FacesApi.getPersons(self.user_data, page=2, pageSize=50)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        personCreateTimeList.extend([person['create_time'] for person in reply.json['persons']])
        self.assertEqual(personCreateTimeList, sorted(personCreateTimeList, reverse=True))

    def test_get_persons_externalid(self):
        """
            :description: Get persons with external id.
            :resources: '/persons'
        """
        externalId = 'test_external_id_123 {}'.format(str(uuid4()))
        personId = self.FacesApi.createPerson(self.account_id, externalId=externalId).json['person_id']
        self.persons.append(personId)
        reply = self.FacesApi.getPersons(externalId=externalId)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        self.assertEqual(reply.json['count'], 1)

    def test_get_persons_nonexist_externalid(self):
        """
            :description: Get persons with non existing external id.
            :resources: '/persons'
        """
        nonexistExternalId = str(uuid4())
        reply = self.FacesApi.getPersons(externalId=nonexistExternalId)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        self.assertEqual(reply.json['count'], 0)

    def test_get_persons_by_face_ids(self):
        """
            :description: Get persons by face ids.
            :resources: '/persons'
        """
        faceId = self.createFace(str(uuid4()))
        personId = self.createPerson()
        self.FacesApi.linkFaceToPerson(faceId=faceId, personId=personId, raiseError=True)
        reply = self.FacesApi.getPersons(faceIds=[faceId])
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.json['count'], 1)
        self.assertEqual(reply.json['persons'][0]['person_id'], personId)

    def test_get_persons_by_nonexists_face_ids(self):
        """
            :description: Get persons by non exists face ids.
            :resources: '/persons'
        """
        reply = self.FacesApi.getPersons(faceIds=[str(uuid4())])
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.json['count'], 0)

    def test_get_persons_by_exists_and_nonexists_face_ids(self):
        """
            :description: Get persons by exists and non exists face ids.
            :resources: '/persons'
        """
        faceId = self.createFace(str(uuid4()))
        personId = self.createPerson()
        self.FacesApi.linkFaceToPerson(faceId=faceId, personId=personId, raiseError=True)
        reply = self.FacesApi.getPersons(faceIds=[faceId, str(uuid4())])
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.json['count'], 1)
        self.assertEqual(reply.json['persons'][0]['person_id'], personId)

    def test_get_persons_by_face_ids_bad_format(self):
        """
            :description: Get persons by non exists face ids.
            :resources: '/persons'
        """
        reply = self.FacesApi.getPersons(faceIds=123)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['face_ids', str(123) + ' is not of type \'string\''])

    def test_delete_persons(self):
        """
            :description: Delete persons.
            :resources: '/persons'
        """
        reply = self.FacesApi.deletePersons(personIds=self.personIds)
        self.assertEqual(reply.statusCode, 204)
        for personId in self.personIds:
            reply = self.FacesApi.getList(personId)
            self.assertErrorRestAnswer(reply, 404, Error.ListNotFound)

    def test_delete_persons_nonexists_listids(self):
        """
            :description: Delete non-existing persons.
            :resources: '/persons'
        """
        self.FacesApi.deletePersons(personIds=self.personIds)

        reply = self.FacesApi.deletePersons(self.personIds)
        self.assertErrorRestAnswer(reply, 400, Error.PersonsNotFound)

    def test_delete_persons_nonexists_accountid(self):
        """
            :description: Delete persons with nonexists accountId.
            :resources: '/persons'
        """
        reply = self.FacesApi.deletePersons(personIds=self.personIds, accountId=str(uuid4()))
        self.assertErrorRestAnswer(reply, 400, Error.PersonsNotFound)

    def test_delete_persons_badformat_accountid(self):
        """
            :description: Delete persons.
            :resources: '/persons'
        """
        badAccountId = 123
        reply = self.FacesApi.deletePersons(personIds=self.personIds, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId) + ' is not of type \'string\''])

    def test_get_persons_timelt(self):
        """
            :description: Get persons with timeLt.
            :resources: '/persons'
        """
        # need sleep to prevent equal time for events and timestamp for filter
        sleep(0.001)
        timeLt = self.getCurrentTimeStamp()
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(personId)
        reply = self.FacesApi.getPersons(accountId=self.account_id, timeLt=timeLt)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        replyPersonsIds = [person['person_id'] for person in reply.json['persons']]
        for personId_ in self.personIds:
            self.assertIn(personId_, replyPersonsIds)
        self.assertNotIn(personId, replyPersonsIds)

    def test_get_persons_badformat_timelt(self):
        """
            :description: Get persons with bad format timeLt.
            :resources: '/persons'
        """
        badTimeLt = str(uuid4())
        reply = self.FacesApi.getPersons(accountId=self.account_id, timeLt=badTimeLt)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['time__lt', str(badTimeLt) + ' is not of type \'string\''])

    def test_get_persons_timegte(self):
        """
            :description: Get persons with timeGte.
            :resources: '/persons'
        """
        # need sleep to prevent equal time for events and timestamp for filter
        sleep(0.001)
        timeGte = self.getCurrentTimeStamp()
        self.personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(self.personId)
        reply = self.FacesApi.getPersons(accountId=self.account_id, timeGte=timeGte)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        self.assertEqual(reply.json['count'], 1)
        self.assertEqual(reply.json['persons'][0]['person_id'], self.personId)

    def test_get_persons_badformat_timegte(self):
        """
            :description: Get persons with bad format timeLt.
            :resources: '/persons'
        """
        badTimeGte = str(uuid4())
        reply = self.FacesApi.getPersons(accountId=self.account_id, timeGte=badTimeGte)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['time__gte', str(badTimeGte) + ' is not of type \'string\''])

    def test_get_persons_time(self):
        """
            :description: Get persons with timeLt, timeGte.
            :resources: '/persons'
        """
        # need sleep to prevent equal time for events and timestamp for filter
        sleep(0.001)
        timeGte = self.getCurrentTimeStamp()
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(personId)
        sleep(0.001)
        timeLt = self.getCurrentTimeStamp()
        reply = self.FacesApi.getPersons(accountId=self.account_id, timeLt=timeLt, timeGte=timeGte)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        self.assertEqual(reply.json['count'], 1)
        self.assertEqual(reply.json['persons'][0]['person_id'], personId)

    def test_get_persons_time_format(self):
        """
            :description: Get persons with timeLt in UTC and LOCAL formats.
            :resources: '/persons'
        """
        for timeFormat in ('LOCAL', 'UTC'):
            with self.subTest(timeFormat=timeFormat):
                # need sleep to prevent equal time for events and timestamp for filter
                sleep(0.001)
                timeLt = self.getCurrentTimeStamp(timeFormat)
                personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
                self.persons.append(personId)
                reply = self.FacesApi.getPersons(accountId=self.account_id, timeLt=timeLt)
                self.validateJson(reply.json, SCHEMA_GET_PERSONS)
                replyPersonsIds = [person['person_id'] for person in reply.json['persons']]
                for personId_ in self.personIds:
                    self.assertIn(personId_, replyPersonsIds)
                self.assertNotIn(personId, replyPersonsIds)

    def test_persons_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/persons'
        """
        self.methods_test('/persons', ['post', 'get', 'delete'])

    def test_get_persons_personids(self):
        """
            :description: Get persons with nonexists personIds.
            :resources: '/persons'
        """
        reply = self.FacesApi.getPersons(accountId=self.account_id, personIds=self.personIds)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        replyPersonIds = [person['person_id'] for person in reply.json['persons']]
        for personId in self.personIds:
            self.assertIn(personId, replyPersonIds)

    def test_get_persons_nonexists_personids(self):
        """
            :description: Get persons with nonexists personIds.
            :resources: '/persons'
        """
        reply = self.FacesApi.getPersons(personIds=[str(uuid4())])
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SCHEMA_GET_PERSONS)
        self.assertEqual(reply.json['count'], 0)
        self.assertEqual(len(reply.json['persons']), 0)
