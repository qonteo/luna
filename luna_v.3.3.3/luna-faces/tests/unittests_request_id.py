from tests.classes import TestBase
from datetime import datetime
from uuid import uuid4
import re


REQUEST_ID_REGEXP = re.compile('^[0-9]{10},[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}\Z', re.I)


def checkRequestId(requestId):

    match = REQUEST_ID_REGEXP.match(requestId)
    return match is not None


class TestRequestId(TestBase):
    """
    Test getVersion
    """
    def test_server_requestid(self):
        """
            :description: Getting the version to check requestId with no requestId in request
            :resources: '/version'
        """
        reply = self.FacesApi.getVersion()
        self.assertTrue(checkRequestId(reply.headers['Luna-Request-Id']))

    def test_badformat_requestid(self):
        """
            :description: Getting the version to check requestId with bad format requestId in request
            :resources: '/version'
        """
        requestId = 'bad format request id'
        reply = self.FacesApi.getVersion(lunaRequestId=requestId)
        self.assertTrue(checkRequestId(reply.headers['Luna-Request-Id']))

    def test_requestid(self):
        """
            :description: Getting the version to check requestId
            :resources: '/version'
        """
        requestId = str(int(datetime.timestamp(datetime.now()))) + ',' + str(uuid4())
        reply = self.FacesApi.getVersion(lunaRequestId=requestId)
        self.assertEqual(requestId, reply.headers['Luna-Request-Id'])
