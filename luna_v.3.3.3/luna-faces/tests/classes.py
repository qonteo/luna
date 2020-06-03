import unittest
from datetime import datetime
from typing import Optional
from uuid import uuid4

import requests
from dateutil import tz
from jsonschema import validate
from luna3.faces.faces import FacesApi

from tests.config import SERVER_ORIGIN, SERVER_API_VERSION, STORAGE_TIME


class TestBase(unittest.TestCase):

    def setUp(self):
        self.user_data = 'test_user_data'
        self.account_id = str(uuid4())
        self.attributes_id = str(uuid4())
        self.event_id = str(uuid4())
        self.payload = {
            'user_data': self.user_data,
            'account_id': self.account_id,
            'attributes_id': self.attributes_id,
            'event_id': self.event_id,
        }
        self.FacesApi = FacesApi(origin=SERVER_ORIGIN, api=SERVER_API_VERSION)
        self.faces = []
        self.lists = []
        self.persons = []

    def updateParams(self):
        self.user_data += '_upd'
        self.attributes_id = str(uuid4())
        self.event_id = str(uuid4())
        self.payload = {
            'user_data': self.user_data,
            'account_id': self.account_id,
            'attributes_id': self.attributes_id,
            'event_id': self.event_id,
        }

    def tearDown(self):
        if len(self.lists):
            self.FacesApi.deleteLists(listIds=self.lists)
        if len(self.faces):
            self.FacesApi.deleteFaces(faceIds=self.faces)
        if len(self.persons):
            self.FacesApi.deletePersons(personIds = self.persons)

    @staticmethod
    def getCurrentTimeStamp(storageTimeForTest=None):
        """
            Function returns time (local or UTC, depends on storageTimeForTest or TIME_STORAGE in config)

            :storageTimeForTest: UTC or LOCAL | overrides STORAGE_TIME from config
            :return: string with timestamp if format '%Y-%m-%dT%H:%M:%S.%fZ'
        """
        if storageTimeForTest is None:
            return datetime.utcnow().isoformat('T') + 'Z' if STORAGE_TIME == 'LOCAL' else datetime.now().replace(
                tzinfo=tz.tzlocal()).isoformat()
        else:
            if storageTimeForTest == 'LOCAL':
                return datetime.now().replace(tzinfo=tz.tzlocal()).isoformat('T')
            else:
                return datetime.utcnow().isoformat('T') + 'Z'

    def assertErrorRestAnswer(self, reply, statusCode, error, msgFormat=None):
        self.assertEqual(statusCode, reply.statusCode, reply.text)
        self.assertEqual(error.description, reply.json['desc'])
        if msgFormat is None:
            self.assertEqual(error.detail, reply.json['detail'])
        else:
            self.assertEqual(error.detail.format(*msgFormat), reply.json['detail'])
        self.assertEqual(error.errorCode, reply.json['error_code'])

    def methods_test(self, resource, allowedMethods):
        """
            :description: Test error: method not allowed
            :resources: '/version'
        """
        methods = 'post', 'put', 'patch', 'delete', 'head', 'get', 'options'

        notAllowedMethods = [method for method in methods if method not in allowedMethods]

        if resource != '/version':
            resource = '/' + str(SERVER_API_VERSION) + resource
        url = SERVER_ORIGIN + resource

        for method in notAllowedMethods:
            if method == 'post':
                reply = requests.post(url)
            elif method == 'put':
                reply = requests.put(url)
            elif method == 'patch':
                reply = requests.patch(url)
            elif method == 'delete':
                reply = requests.delete(url)
            elif method == 'head':
                reply = requests.head(url)
            elif method == 'get':
                reply = requests.get(url)
            elif method == 'options':
                reply = requests.options(url)
            self.assertEqual(reply.status_code, 405)
            self.assertEqual(reply.reason, 'Method Not Allowed')

    @staticmethod
    def validateJson(data, schema):
        """
        Validate json.
        :param data: json for validation
        :param schema: json schema
        :raise VLException(Error.BadInputJson, 400): if failed  to validate schema
        """
        validate(data, schema)

    def createFace(self, attributesId: Optional[str], ) -> str:
        faceId = self.FacesApi.createFace(self.account_id, attributesId=attributesId, raiseError=True).json['face_id']
        self.faces.append(faceId)
        return faceId

    def createPerson(self) -> str:
        personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
        self.persons.append(personId)
        return personId
