import unittest
import requests
import time

from tests.config import SERVER_ORIGIN, SERVER_API_VERSION

SERVER_URL = "{}/{}".format(SERVER_ORIGIN, SERVER_API_VERSION)


class TestHeaders(unittest.TestCase):
    """
    Test headers
    """
    def test_check_custom_luna_req_id(self):
        """
        .. test:: test_check_custom_luna_req_id

            :resources: "/"
            :description: success setting LUNA-Request-Id
            :LIS: No
            :tag: Headers
        """
        requestId = "{},{}".format(int(time.time()), "11111111-1111-4a11-8111-111111111111")
        replyInfo = requests.get(url=SERVER_URL, headers={"LUNA-Request-Id": requestId})
        self.assertEqual(replyInfo.headers["LUNA-Request-Id"], requestId)


    def test_check_luna_req_id(self):
        """
        .. test:: test_check_luna_req_id

            :description: success getting LUNA-Request-Id
            :LIS: No
            :tag: Headers
            :resources: "/"
        """

        replyInfo = requests.get(url=SERVER_URL)
        self.assertIn("LUNA-Request-Id", replyInfo.headers)
        rid = replyInfo.headers['LUNA-Request-Id']
        requestId = rid.split(",")
        self.assertTrue(abs(time.time()-int(requestId[0])) < 2, "too much difference between time")
        self.assertEqual(len(requestId[1]), 36)

    def test_check_custom_bad_luna_req_id(self):

        """
        .. test:: test_check_custom_bad_luna_req_id

            :resources: "/"
            :description: bad setting LUNA-Request-Id
            :LIS: No
            :tag: Headers
        """
        requestId = "{},{}".format(int(time.time()), "11111111-1111-4a11-8111-111111111111x")
        replyInfo = requests.get(url=SERVER_URL, headers={"LUNA-Request-Id": requestId})
        self.assertTrue(replyInfo.headers["LUNA-Request-Id"] != requestId)
