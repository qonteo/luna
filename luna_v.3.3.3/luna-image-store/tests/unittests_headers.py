import requests

from tests.base_class import SERVER_ORIGIN
import unittest
from time import time
from uuid import uuid4


class TestHeaders(unittest.TestCase):
    """
    Test headers
    """

    def test_check_custom_luna_req_id(self):
        """
        .. test:: test_check_custom_luna_req_id

            :resources: "/"
            :description: success setting LUNA-Request-Id
            :S3: No
            :tag: Headers
        """
        customRequestId = "{},{}".format(int(time()), str(uuid4()))
        replyInfo = requests.get(url=SERVER_ORIGIN, headers={"LUNA-Request-Id": customRequestId})
        self.assertEqual(replyInfo.headers["LUNA-Request-Id"], customRequestId)

    def test_check_luna_req_id(self):
        """
        .. test:: test_check_luna_req_id

            :description: success getting LUNA-Request-Id
            :S3: No
            :tag: Headers
            :resources: "/"
        """
        replyInfo = requests.get(url=SERVER_ORIGIN)
        self.assertIn("LUNA-Request-Id", replyInfo.headers)
        rid = replyInfo.headers['LUNA-Request-Id']
        requestId = rid.split(",")
        self.assertTrue(abs(time() - int(requestId[0])) < 2, "too much difference between time")
        self.assertEqual(len(requestId[1]), 36)
