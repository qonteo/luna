import unittest

from base_class import BaseClass
import time

from utils.common.config_loader import ConfigLoader


class TestLongTask(BaseClass):
    @unittest.skipIf(not int(ConfigLoader.get_property("test_long_task")), "disable long task")
    def test_all_objects_in_task(self):
        for task_type in ("descriptors", "reextract"):
            with self.subTest(task_type = task_type):
                if task_type == "reextract":
                    response = TestLongTask.admin_client.start_reextract_descriptors()
                else:
                    response = TestLongTask.admin_client.start_gc({"task_type": task_type,
                                                                   "target": "all"})
                self.assertEqual(201, response.status_code)
                task_id = response.content["task_id"]
                for i in range(180):
                    time.sleep(1)
                    response = TestLongTask.admin_client.get_task(task_id)
                    self.assertEqual(200, response.status_code)
                    if float(response.content["task_info"]["progress"]) == 1.0:
                        break
                else:
                    self.fail("task did not end")

    @unittest.skipIf(not int(ConfigLoader.get_property("test_long_task")), "disable long task")
    def test_stop_long_task(self):
        for task_type in ("descriptors", "reextract"):
            with self.subTest(task_type = task_type):
                if task_type == "reextract":
                    response = TestLongTask.admin_client.start_reextract_descriptors()
                else:
                    response = TestLongTask.admin_client.start_gc({"task_type": task_type,
                                                                   "target": "all"})
                task_id = response.content["task_id"]
                TestLongTask.admin_client.stop_task(task_id)
                time.sleep(2)
                response = TestLongTask.admin_client.get_task(task_id)
                progress = response.content["task_info"]["progress"]
                self.assertTrue(progress < 1)
                for i in range(10):
                    time.sleep(1)
                    response = TestLongTask.admin_client.get_task(task_id)
                    self.assertEqual(progress, response.content["task_info"]["progress"])
