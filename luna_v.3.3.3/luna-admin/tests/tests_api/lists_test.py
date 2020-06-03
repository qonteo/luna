from base_class import BaseClass
from schemas import LISTS_SCHEMA



class TestLists(BaseClass):
    person_list2 = None
    descriptor_list = None
    person_list1 = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.person_list2 = TestLists.employer.api_client.createList(listType ="persons").body["list_id"]
        cls.descriptor_list = TestLists.employer.api_client.createList(listType ="descriptors").body[
            "list_id"]
        cls.person_list1 = TestLists.employer.api_client.createList(listType ="persons").body["list_id"]

    def test_get_lists(self):
        response = TestLists.admin_client.get_lists()

        self.assertEqual(response.status_code, 200)
        self.assertSchema(response.content, LISTS_SCHEMA)

    def test_get_lists_of_account(self):
        response = TestLists.admin_client.get_lists({"account_id": TestLists.employer.account_id})

        self.assertEqual(response.status_code, 200)
        self.assertSchema(response.content, LISTS_SCHEMA)
        self.assertSetEqual(set([account_list["list_id"] for account_list in response.content["lists"]]),
                            {TestLists.person_list2, TestLists.descriptor_list,
                             TestLists.person_list1})

    def test_get_lists_with_pagination(self):
        response = TestLists.admin_client.get_lists({"account_id": TestLists.employer.account_id,
                                                     "page": 1, "page_size": 2})
        self.assertSchema(response.content, LISTS_SCHEMA)
        self.assertEqual(2, len(response.content["lists"]))
        response = TestLists.admin_client.get_lists({"account_id": TestLists.employer.account_id,
                                                     "page": 2, "page_size": 2})
        self.assertEqual(1, len(response.content["lists"]))

    def test_get_list_by_type(self):
        lists = [{"type": 1, "list_ids": [TestLists.person_list2,
                                          TestLists.person_list1]},
                 {"type": 0, "list_ids": [TestLists.descriptor_list]}]
        for list_type in lists:
            with self.subTest(state = list_type["type"]):
                response = TestLists.admin_client.get_lists({"account_id": TestLists.employer.account_id,
                                                             "type": list_type["type"]})
                self.assertEqual(response.status_code, 200)
                self.assertSchema(response.content, LISTS_SCHEMA)
                self.assertSetEqual(set([account_list["list_id"] for account_list in response.content["lists"]]),
                                    set(list_type["list_ids"]))

    def test_get_lists_bad_params(self):
        bad_params = {"page": "a", "page_size": "a", "account_id": "112"}
        self.badParamTests(bad_params, BaseClass.admin_client.get_lists)

    def test_method_not_allowed(self):
        self.methodNotAllowed("{}/lists".format(BaseClass.admin_client.url),
                              ["post", "put", "delete"])
