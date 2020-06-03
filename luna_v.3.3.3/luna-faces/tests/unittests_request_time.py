from tests.classes import TestBase
from time import time


class TestRequestTime(TestBase):
    """
    Test get request time
    """
    def test_server_request_time(self):
        """
            :description: Getting the version to check Begin-Request-Time and End-Request-Time headers
            :resources: '/version'
        """
        reply = self.FacesApi.getVersion()
        self.assertTrue("End-Request-Time" in reply.headers)
        self.assertTrue("Begin-Request-Time" in reply.headers)
        beginTime = float(reply.headers["Begin-Request-Time"])
        endTime= float(reply.headers["End-Request-Time"])
        self.assertLessEqual(beginTime, endTime)
        self.assertAlmostEqual(time(), beginTime, 1)
        self.assertAlmostEqual(time(), endTime, 1)
