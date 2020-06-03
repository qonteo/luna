import unittest
import requests
from utils.common.config_loader import ConfigLoader
from luna_admin.crutches_on_wheels.utils.regexps import REQUEST_ID_REGEXP
from time import time, timezone


LPS_ADMIN_URL = ConfigLoader.get_admin_url()


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
        requestId = "{},{}".format(int(time()), "11111111-1111-4a11-8111-111111111111")
        replyInfo = requests.get(url=LPS_ADMIN_URL, headers={"LUNA-Request-Id": requestId})
        self.assertEqual(replyInfo.headers["LUNA-Request-Id"], requestId)

    def test_check_luna_req_id(self):
        """
        .. test:: test_check_luna_req_id

            :description: success getting LUNA-Request-Id
            :LIS: No
            :tag: Headers
            :resources: "/"
        """
        replyInfo = requests.get(url=LPS_ADMIN_URL)
        self.assertIn("LUNA-Request-Id", replyInfo.headers)
        rid = replyInfo.headers['LUNA-Request-Id']
        requestId = rid.split(",")
        self.assertTrue(abs(time()-timezone-int(requestId[0])) < 2, "too much difference between time")
        self.assertEqual(len(requestId[1]), 36)

    def test_check_custom_bad_luna_req_id(self):

        """
        .. test:: test_check_custom_bad_luna_req_id

            :resources: "/"
            :description: bad setting LUNA-Request-Id
            :LIS: No
            :tag: Headers
        """
        requestId = "{},{}".format(int(time()), "11111111-1111-4a11-8111-111111111111x")
        replyInfo = requests.get(url = LPS_ADMIN_URL, headers = {"LUNA-Request-Id": requestId})
        self.assertTrue(replyInfo.headers["LUNA-Request-Id"] != requestId)
        self.assertTrue(REQUEST_ID_REGEXP.match(replyInfo.headers["LUNA-Request-Id"]) is not None)
