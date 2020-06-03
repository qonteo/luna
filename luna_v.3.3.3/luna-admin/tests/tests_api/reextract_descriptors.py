import unittest

import datetime
import requests
from utils.common.config_loader import ConfigLoader
from base_class import BaseClass
import time
from uuid import uuid4


class TestReExtract(BaseClass):
    def assert_done_task(self, task_id, error_count = 0):
        response = TestReExtract.admin_client.get_task(task_id)
        self.assertEqual(200, response.status_code)
        self.assertTaskInfo(response.content["task_info"], task_id, "list descriptors", error_count)

    def assert_image_not_found(self, task_id, descriptors):
        response = TestReExtract.admin_client.get_task_errors(task_id)
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(descriptors), response.content["error_count"])
        notFoundImages = [error['message'].split("Object not found, target id: ")[1] for error in
                          response.content["errors"]]
        self.assertSetEqual(set(descriptors), set(notFoundImages))

    def check_descriptor_in_new_core(self, descriptor_id):
        new_luna = ConfigLoader.get_property("reextract_luna_core_url")
        response = requests.get("{}/descriptors?id={}".format(new_luna, descriptor_id))
        self.assertEqual(200, response.status_code)

    @unittest.skipIf(not ConfigLoader.get_int_property("test_reextract"), "disable re-extract tests")
    def test_reextract_several_descriptors(self):
        descriptor_1 = self.createDescriptor(TestReExtract.employer)
        descriptor_2 = self.createDescriptor(TestReExtract.employer)

        response = TestReExtract.admin_client.start_reextract_descriptors({"descriptors": [descriptor_1, descriptor_2]})
        self.assertEqual(201, response.status_code)
        task_id = response.content["task_id"]
        time.sleep(2)
        self.assert_done_task(task_id)
        for descriptor in (descriptor_1, descriptor_2):
            self.check_descriptor_in_new_core(descriptor)

    @unittest.skipIf(not ConfigLoader.get_int_property("test_reextract"), "disable re-extract tests")
    def test_bad_json(self):
        error_cases = [{"params": {"descriptor": [str(uuid4()), str(uuid4())]}},
                       {"params": {"descriptors": str(uuid4())}},
                       {"params": {"descriptors": [str(uuid4()), "aaa"]}},
                       ]
        for error_case in error_cases:
            with self.subTest(params = error_case["params"]):
                response = TestReExtract.admin_client.start_reextract_descriptors(error_case["params"])

                self.assertEqual(400, response.status_code)
                self.assertEqual(response.content["error_code"], 12022)
                self.assertTrue(response.content["detail"].startswith("Failed to validate input json. Path:"))

    @unittest.skipIf(not ConfigLoader.get_int_property("test_reextract"), "disable re-extract tests")
    def test_reextract_non_exist_descriptor(self):
        descriptor_1 = self.createDescriptor(TestReExtract.employer)
        descriptor_2 = str(uuid4())
        descriptor_3 = str(uuid4())

        response = TestReExtract.admin_client.start_reextract_descriptors({"descriptors": [descriptor_1, descriptor_2,
                                                                                           descriptor_3]})
        task_id = response.content["task_id"]

        time.sleep(2)

        self.assertEqual(201, response.status_code)
        self.assert_done_task(task_id, 2)
        self.assert_image_not_found(task_id, [descriptor_2, descriptor_3])
