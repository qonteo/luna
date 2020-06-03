from tests.classes import TestBase
from uuid import uuid4
from datetime import timedelta
from luna_faces.crutches_on_wheels.errors.errors import Error
from tests.shemas import SHEMA_CREATE_FACE, SHEMA_GET_FACES
from time import sleep
from dateutil import parser, tz


DEFAULT_FACES_COUNT = 3
PAGE_SIZE = 100


class TestFaces(TestBase):
    """
    Test Lists
    """
    def setUp(self):
        TestBase.setUp(self)
        self.faceIds = []
        for _ in range(DEFAULT_FACES_COUNT):
            faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()),
                                              userData=self.user_data, raiseError=True).json['face_id']
            self.faceIds.append(faceId)
            self.faces.append(faceId)

    def test_create_face(self):
        """
            :description: Create face.
            :resources: '/faces'
        """
        reply = self.FacesApi.createFace(self.account_id, self.attributes_id, self.event_id, self.user_data)
        self.faces.append(reply.json['face_id'])
        self.validateJson(reply.json, SHEMA_CREATE_FACE)

        createTime = self.FacesApi.getFace(reply.json['face_id']).json['create_time']
        delta_time = parser.parse(self.getCurrentTimeStamp()).replace(tzinfo=None) - \
                     parser.parse(createTime).astimezone(tz.tzlocal()).replace(tzinfo=None)
        self.assertTrue(delta_time < timedelta(seconds=2))

    def test_create_face_without_attributes(self):
        """
            :description: Create face without attributes.
            :resources: '/faces'
        """
        reply = self.FacesApi.createFace(self.account_id)

        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['', '\'attributes_id\' is a required property'])

    def test_create_face_max_userdata(self):
        """
            :description: Create face with max size of user_data.
            :resources: '/faces'
        """
        reply = self.FacesApi.createFace(self.account_id, self.attributes_id, self.event_id, 'x'*128)
        self.faces.append(reply.json['face_id'])
        self.assertEqual(reply.statusCode, 201)
        self.validateJson(reply.json, SHEMA_CREATE_FACE)

        reply = self.FacesApi.getFace(reply.json['face_id'])
        self.assertEqual(reply.json["user_data"], 'x'*128)

    def test_create_face_excessive_userdata(self):
        """
            :description: Create face with user_data with size > max.
            :resources: '/faces'
        """
        reply = self.FacesApi.createFace(self.account_id, self.attributes_id, self.event_id, 'x'*129)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', '\''+'x'*129+'\''+' is too long'])

    def test_create_face_excessive_external_id(self):
        """
            :description: Create face with external_id with size > max.
            :resources: '/faces'
        """
        reply = self.FacesApi.createFace(self.account_id, self.attributes_id, self.event_id, externalId= 'x'*37)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['external_id', '\''+'x'*37+'\''+' is too long'])

    def test_create_face_badformat_userdata(self):
        """
            :description: Create face with bad format user data.
            :resources: '/faces'
        """
        badUserData = 123
        reply = self.FacesApi.createFace(self.account_id, self.attributes_id, self.event_id, badUserData)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['user_data', str(badUserData) + ' is not of type \'string\''])

    def test_create_face_badformat_accountid(self):
        """
            :description: Create face with bad format accountId.
            :resources: '/faces'
        """
        badAccountId = 123
        reply = self.FacesApi.createFace(badAccountId, self.attributes_id, self.event_id, self.user_data)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_create_face_badformat_attributesid(self):
        """
            :description: Create face with bad format attriburesId.
            :resources: '/faces'
        """
        badAttributesId = 123
        reply = self.FacesApi.createFace(self.account_id, badAttributesId, self.event_id, self.user_data)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['attributes_id', str(badAttributesId)+' is not of type \'string\''])

    def test_create_face_badformat_eventid(self):
        """
            :description: Create face with bad format eventId.
            :resources: '/faces'
        """
        badEventId = 123
        reply = self.FacesApi.createFace(self.account_id, self.attributes_id, badEventId, self.user_data)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['event_id', str(badEventId)+' is not of type \'string\''])

    def test_create_faces_attributes_alreadyexists(self):
        """
            :description: Create face with already exists attriburesId.
            :resources: '/faces'
        """
        reply = self.FacesApi.createFace(self.account_id, self.attributes_id, self.event_id, self.user_data)
        self.faces.append(reply.json['face_id'])

        reply = self.FacesApi.createFace(self.account_id, self.attributes_id, self.event_id, self.user_data)
        self.assertErrorRestAnswer(reply, 409, Error.FaceWithAttributeOrIdAlreadyExist)

    def test_create_face_badformat_externalid(self):
        """
            :description: Create face with bad format external id.
            :resources: '/faces'
        """
        badformatExternalId = 123
        reply = self.FacesApi.createFace(self.account_id, self.attributes_id, externalId=badformatExternalId)
        self.assertErrorRestAnswer(reply, 400, Error.BadInputJson,
                                   msgFormat=['external_id', str(badformatExternalId)+' is not of type \'string\''])

    def test_get_faces(self):
        """
            :description: Get faces.
            :resources: '/faces'
        """
        reply = self.FacesApi.getFaces()
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)

    def test_get_faces_partuserdata(self):
        """
            :description: Get faces.
            :resources: '/faces'
        """
        reply = self.FacesApi.getFaces(userData=self.user_data[:len(self.user_data) // 2])
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)

    def test_get_faces_nonexists_userdata(self):
        """
            :description: Get faces.
            :resources: '/faces'
        """
        nonexistsUserData = str(uuid4())
        reply = self.FacesApi.getFaces(nonexistsUserData)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        self.assertEqual(reply.json['count'], 0)

    def test_get_faces_accountids(self):
        """
            :description: Get faces with accountID.
            :resources: '/faces'
        """
        self.faceId = self.FacesApi.createFace(accountId=str(uuid4()), attributesId=str(uuid4())).json['face_id']
        self.faces.append(self.faceId)
        reply = self.FacesApi.getFaces(accountId=self.account_id)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        replyFacesIds = [face['face_id'] for face in reply.json['faces']]
        for faceId in self.faceIds:
            self.assertIn(faceId, replyFacesIds)
        self.assertNotIn(self.faceId, replyFacesIds)

    def test_get_faces_nonexists_accountids(self):
        """
            :description: Get faces with nonexists accountID.
            :resources: '/faces'
        """
        reply = self.FacesApi.getFaces(accountId=str(uuid4()))
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        self.assertEqual(reply.json['count'], 0)

    def test_get_faces_badformat_accountid(self):
        """
            :description: Get faces with bad format accountID.
            :resources: '/faces'
        """
        badAccountId = 123
        reply = self.FacesApi.getFaces(accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_get_faces_eventid(self):
        """
            :description: Get faces with eventId.
            :resources: '/faces'
        """
        self.faceId = self.FacesApi.createFace(self.account_id, self.attributes_id,
                                               eventId=self.event_id).json['face_id']
        self.faces.append(self.faceId)
        reply = self.FacesApi.getFaces(eventId=self.event_id)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.json['count'], 1)
        self.assertEqual(self.faceId, reply.json['faces'][0]['face_id'])

    def test_get_faces_nonexists_eventid(self):
        """
            :description: Get faces with non-existing eventId.
            :resources: '/faces'
        """
        nonExistsEventId = str(uuid4())
        reply = self.FacesApi.getFaces(eventId=nonExistsEventId)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.json['count'], 0)
        self.validateJson(reply.json, SHEMA_GET_FACES)

    def test_get_faces_badformat_eventid(self):
        """
            :description: Get faces with bad format eventId.
            :resources: '/faces'
        """
        badEventId = 123
        reply = self.FacesApi.getFaces(eventId=badEventId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['event_id', str(badEventId)+' is not of type \'string\''])

    def test_get_faces_listid(self):
        """
            :description: Get faces with non-existing listId.
            :resources: '/faces'
        """
        self.faceId = self.FacesApi.createFace(self.account_id, self.attributes_id).json['face_id']
        self.faces.append(self.faceId)
        self.listId = self.FacesApi.createList(self.account_id, self.user_data).json['list_id']
        self.lists.append(self.listId)
        self.FacesApi.link(self.listId, [self.faceId], action =  'attach', accountId = self.account_id,
                           raiseError = True)
        reply = self.FacesApi.getFaces(listId=self.listId)
        self.assertEqual(reply.statusCode, 200)
        replyFaceIds = [face['face_id'] for face in reply.json['faces']]
        self.assertIn(self.faceId, replyFaceIds)
        for faceId in self.faceIds:
            self.assertNotIn(faceId, replyFaceIds)

    def test_get_faces_nonexists_listid(self):
        """
            :description: Get faces with non-existing listId.
            :resources: '/faces'
        """
        nonExistsListId = str(uuid4())
        reply = self.FacesApi.getFaces(listId=nonExistsListId)
        self.assertEqual(reply.statusCode, 200)
        self.assertEqual(reply.json['count'], 0)
        self.validateJson(reply.json, SHEMA_GET_FACES)

    def test_get_faces_badformat_listid(self):
        """
            :description: Get faces with bad format listId.
            :resources: '/faces'
        """
        badListId = 123
        reply = self.FacesApi.getFaces(listId=badListId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['list_id', str(badListId)+' is not of type \'string\''])

    def test_get_faces_faceids(self):
        """
            :description: Get faces with nonexists faceIds.
            :resources: '/faces'
        """
        reply = self.FacesApi.getFaces(accountId=self.account_id, faceIds=self.faceIds)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        replyFaceIds = [face['face_id'] for face in reply.json['faces']]
        for faceId in self.faceIds:
            self.assertIn(faceId, replyFaceIds)

    def test_get_faces_nonexists_faceids(self):
        """
            :description: Get faces with nonexists faceIds.
            :resources: '/faces'
        """
        reply = self.FacesApi.getFaces(faceIds=[str(uuid4())])
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        self.assertEqual(reply.json['count'], 0)

    def test_get_faces_badformat_faceids(self):
        """
            :description: Get faces with bad faceIds.
            :resources: '/faces'
        """
        badFaceIds = 123
        reply = self.FacesApi.getFaces(faceIds=badFaceIds)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['face_ids', str(badFaceIds)+' is not of type \'string\''])

    def test_get_faces_timelt(self):
        """
            :description: Get faces with timeLt.
            :resources: '/faces'
        """
        # need sleep to prevent equal time for events and timestamp for filter
        sleep(0.001)
        timeLt = self.getCurrentTimeStamp()
        self.faceId = self.FacesApi.createFace(self.account_id, self.attributes_id, raiseError=True).json['face_id']
        self.faces.append(self.faceId)
        reply = self.FacesApi.getFaces(timeLt=timeLt, accountId = self.account_id, pageSize = 100)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        replyFacesIds = [face['face_id'] for face in reply.json['faces']]
        for faceId in self.faceIds:
            self.assertIn(faceId, replyFacesIds)
        self.assertNotIn(self.faceId, replyFacesIds)

    def test_get_faces_time_format(self):
        """
            :description: Get faces with timeLt in UTC and LOCAL formats.
            :resources: '/faces'
        """
        for timeFormat in ('LOCAL', 'UTC'):
            with self.subTest(timeFormat=timeFormat):
                # need sleep to prevent equal time for events and timestamp for filter
                sleep(0.001)
                timeLt = self.getCurrentTimeStamp(timeFormat)
                self.faceId = self.FacesApi.createFace(self.account_id, str(uuid4()),
                                                       raiseError=True).json['face_id']
                self.faces.append(self.faceId)
                reply = self.FacesApi.getFaces(timeLt=timeLt, accountId=self.account_id, pageSize=100)
                self.validateJson(reply.json, SHEMA_GET_FACES)
                replyFacesIds = [face['face_id'] for face in reply.json['faces']]
                for faceId in self.faceIds:
                    self.assertIn(faceId, replyFacesIds)
                self.assertNotIn(self.faceId, replyFacesIds)

    def test_get_faces_badformat_timelt(self):
        """
            :description: Get face with bad format timeLt.
            :resources: '/faces'
        """
        badTimeLt = str(uuid4())
        reply = self.FacesApi.getFaces(timeLt=badTimeLt)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['time__lt', str(badTimeLt)+' is not of type \'string\''])

    def test_get_faces_timegte(self):
        """
            :description: Get faces with timeGte.
            :resources: '/faces'
        """
        # need sleep to prevent equal time for events and timestamp for filter
        sleep(0.001)
        timeGte = self.getCurrentTimeStamp()
        self.faceId = self.FacesApi.createFace(self.account_id, self.attributes_id, raiseError=True).json['face_id']
        self.faces.append(self.faceId)
        reply = self.FacesApi.getFaces(accountId=self.account_id, timeGte=timeGte)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        self.assertEqual(reply.json['count'], 1)
        self.assertEqual(reply.json['faces'][0]['face_id'], self.faceId)

    def test_get_faces_badformat_timegte(self):
        """
            :description: Get face with bad format timeLt.
            :resources: '/faces'
        """
        badTimeGte = str(uuid4())
        reply = self.FacesApi.getFaces(timeGte=badTimeGte)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['time__gte', str(badTimeGte)+' is not of type \'string\''])

    def test_get_faces_time(self):
        """
            :description: Get faces with timeLt, timeGte.
            :resources: '/faces'
        """
        # need sleep to prevent equal time for events and timestamp for filter
        sleep(0.001)
        timeGte = self.getCurrentTimeStamp()
        self.faceId = self.FacesApi.createFace(self.account_id, self.attributes_id, raiseError=True).json['face_id']
        self.faces.append(self.faceId)
        # need sleep to prevent equal time for events and timestamp for filter
        sleep(0.001)
        timeLt = self.getCurrentTimeStamp()
        reply = self.FacesApi.getFaces(accountId=self.account_id, timeLt=timeLt, timeGte=timeGte)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        self.assertEqual(reply.json['count'], 1)
        self.assertEqual(reply.json['faces'][0]['face_id'], self.faceId)

    def test_get_faces_wrong_time(self):
        """
            :description: Get faces with wrong timeLt, timeGte.
            :resources: '/faces'
        """
        timeGte = self.getCurrentTimeStamp()
        self.faceId = self.FacesApi.createFace(self.account_id, self.attributes_id, raiseError=True).json['face_id']
        self.faces.append(self.faceId)
        timeLt = self.getCurrentTimeStamp()
        reply = self.FacesApi.getFaces(accountId=self.account_id, timeLt=timeGte, timeGte=timeLt)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        self.assertEqual(reply.json['count'], 0)

    def test_get_faces_page_pagesize(self):
        """
            :description: Get faces with max page_size.
            :resources: '/faces'
        """
        reply = self.FacesApi.getFaces(page=1, pageSize=100)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        self.assertGreaterEqual(reply.json['count'], DEFAULT_FACES_COUNT)

    def test_get_faces_page(self):
        """
            :description: Get faces with page=-1.
            :resources: '/faces'
        """
        reply = self.FacesApi.getFaces(page=-1, pageSize=100)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        self.assertGreaterEqual(reply.json['count'], DEFAULT_FACES_COUNT)

    def test_get_faces_bad_pagesize(self):
        """
            :description: Get faces with incorrect page_size.
            :resources: '/faces'
        """
        for _ in range(100):
            faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()),
                                              raiseError=True).json['face_id']
            self.faceIds.append(faceId)
            self.faces.append(faceId)
        reply = self.FacesApi.getFaces(pageSize=1000)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        self.assertGreaterEqual(reply.json['count'], 100)

    def test_get_faces_externalid(self):
        """
            :description: Get faces with external id.
            :resources: '/faces'
        """
        externalId = 'test_external_id_123 {}'.format(str(uuid4()))[:32]
        faceId = self.FacesApi.createFace(self.account_id,
                                          self.attributes_id, externalId=externalId).json['face_id']
        self.faces.append(faceId)
        reply = self.FacesApi.getFaces(externalId=externalId)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        self.assertEqual(reply.json['count'], 1)

    def test_get_faces_nonexist_externalid(self):
        """
            :description: Get faces with non existing external id.
            :resources: '/faces'
        """
        nonexistExternalId = str(uuid4())
        reply = self.FacesApi.getFaces(externalId=nonexistExternalId)
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        self.assertEqual(reply.json['count'], 0)

    def test_get_faces_create_time_sort(self):
        """
            :description: Get faces and check sorting by create_time in recieved list.
            :resources: '/faces'
        """
        for _ in range(100):
            faceId = self.FacesApi.createFace(self.account_id,
                                              attributesId=str(uuid4()), raiseError=True).json['face_id']
            self.faceIds.append(faceId)
            self.faces.append(faceId)
        reply = self.FacesApi.getFaces(pageSize=100)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        faceCreateTimeList = [face['create_time'] for face in reply.json['faces']]
        self.assertEqual(faceCreateTimeList, sorted(faceCreateTimeList, reverse=True))

    def test_get_faces_create_time_sort_pages(self):
        """
            :description: Get faces and check sorting by create_time in recieved lists.
            :resources: '/faces'
        """
        for _ in range(100):
            faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()),
                                              raiseError=True).json['face_id']
            self.faceIds.append(faceId)
            self.faces.append(faceId)
        reply = self.FacesApi.getFaces(page=1, pageSize=50)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        faceCreateTimeList = [face['create_time'] for face in reply.json['faces']]
        reply = self.FacesApi.getFaces(page=2, pageSize=50)
        self.validateJson(reply.json, SHEMA_GET_FACES)
        faceCreateTimeList.extend([face['create_time'] for face in reply.json['faces']])
        self.assertEqual(faceCreateTimeList, sorted(faceCreateTimeList, reverse=True))

    def test_delete_faces(self):
        """
            :description: Delete faces.
            :resources: '/faces'
        """
        reply = self.FacesApi.deleteFaces(faceIds=self.faceIds)
        self.assertEqual(reply.statusCode, 204)
        for faceId in self.faceIds:
            reply = self.FacesApi.getFace(faceId)
            self.assertErrorRestAnswer(reply, 404, Error.FaceNotFound)

    def test_delete_faces_nonexists_faceids(self):
        """
            :description: Delete non-existing faces.
            :resources: '/faces'
        """
        reply = self.FacesApi.deleteFaces([str(uuid4())])
        self.assertErrorRestAnswer(reply, 400, Error.FacesNotFound)

    def test_delete_faces_nonexists_accountid(self):
        """
            :description: Delete faces with nonexists accountId.
            :resources: '/faces'
        """
        reply = self.FacesApi.deleteFaces(faceIds=self.faceIds, accountId=str(uuid4()))
        self.assertErrorRestAnswer(reply, 400, Error.FacesNotFound)

    def test_delete_faces_badformat_accountid(self):
        """
            :description: Delete faces.
            :resources: '/faces'
        """
        badAccountId = 123
        reply = self.FacesApi.deleteFaces(faceIds=self.faceIds, accountId=badAccountId)
        self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                   msgFormat=['account_id', str(badAccountId)+' is not of type \'string\''])

    def test_faces_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/faces'
        """
        self.methods_test('/faces', ['post', 'get', 'delete'])
