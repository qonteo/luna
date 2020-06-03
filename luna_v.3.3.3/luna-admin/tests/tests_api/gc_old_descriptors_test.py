import datetime
import time
from base_class import BaseClass
import dateutil.parser


def update_desc_date(desc_id, date):
    sql_utils = TestGcOldDescriptorsOfAccount.sqlUtils
    sql_utils.execute_update(
        "update face set last_update_time='{0}' where face_id='{1}'".format(date, desc_id)
    )


class TestGcOldDescriptorsOfAccount(BaseClass):
    descriptor_with_person = None
    descriptor_with_list = None
    descriptor_for_remove = None
    free_descriptor_other_account = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        person_id = TestGcOldDescriptorsOfAccount.employer.api_client.createPerson(raiseError = True).body["person_id"]
        cls.descriptor_with_person = BaseClass.createDescriptor(TestGcOldDescriptorsOfAccount.employer)
        TestGcOldDescriptorsOfAccount.employer.api_client.linkDescriptorToPerson(person_id, cls.descriptor_with_person,
                                                                                 raiseError = True)

        list_id = TestGcOldDescriptorsOfAccount.employer.api_client.createList(listType = "descriptors",
                                                                               raiseError = True).body["list_id"]
        cls.descriptor_with_list = BaseClass.createDescriptor(TestGcOldDescriptorsOfAccount.employer)
        TestGcOldDescriptorsOfAccount.employer.api_client.linkListToDescriptor(cls.descriptor_with_list, list_id,
                                                                               raiseError = True)

        cls.descriptor_for_remove = BaseClass.createDescriptor(TestGcOldDescriptorsOfAccount.employer)

        cls.free_descriptor_other_account = BaseClass.createDescriptor(TestGcOldDescriptorsOfAccount.employer2)

        for descriptor_id in (cls.descriptor_for_remove, cls.descriptor_with_list, cls.descriptor_with_person,
                              cls.free_descriptor_other_account):
            update_desc_date(descriptor_id, datetime.datetime.now() - datetime.timedelta(days = 2))

    def assert_done_task(self, task_id, target, targetId):
        response = TestGcOldDescriptorsOfAccount.admin_client.get_task(task_id)
        self.assertEqual(200, response.status_code)
        self.assertTaskInfo(response.content["task_info"], task_id, "{} {}".format(target, targetId), 0)

    def test_gc_descriptors_of_account(self):

        response = TestGcOldDescriptorsOfAccount.admin_client.start_gc({"task_type": "descriptors", "target": "account",
                                                                        "target_id": TestGcOldDescriptorsOfAccount.employer.account_id})
        self.assertEqual(response.status_code, 201)
        time.sleep(2)
        self.assert_done_task(response.content["task_id"], "account", TestGcOldDescriptorsOfAccount.employer.account_id)
        reply = TestGcOldDescriptorsOfAccount.employer.api_client.getDescriptor(
            TestGcOldDescriptorsOfAccount.descriptor_for_remove)
        self.assertEqual(reply.statusCode, 404)
        for descriptor in ([TestGcOldDescriptorsOfAccount.descriptor_with_person,
                            TestGcOldDescriptorsOfAccount.descriptor_with_list]):
            reply = TestGcOldDescriptorsOfAccount.employer.api_client.getDescriptor(descriptor)
            self.assertEqual(reply.statusCode, 200)
        reply = TestGcOldDescriptorsOfAccount.employer2.api_client.getDescriptor(
            TestGcOldDescriptorsOfAccount.free_descriptor_other_account)
        self.assertEqual(reply.statusCode, 200)

    def test_gc_descriptors_bad_param(self):
        bad_params = [{"params": {"task_type": "descriptors", "target": "accounts",
                                  "target_id": TestGcOldDescriptorsOfAccount.employer.account_id}, "name": "target"},
                      {"params": {"task_type": "descriptors", "target": "account", "target_id": "111"},
                       "name": "target_id"}]
        response = TestGcOldDescriptorsOfAccount.admin_client.start_gc(bad_params[0]["params"])
        self.assertBadParam(response.content, bad_params[0]["name"])
