from base_class import BaseClass
from schemas import ACCOUNTS_SCHEMA


class TestAccounts(BaseClass):

    def test_get_accounts(self):
        response = TestAccounts.admin_client.get_accounts()

        self.assertEqual(response.status_code, 200)
        self.assertSchema(response.content, ACCOUNTS_SCHEMA)
        self.assertTrue(len(response.content["accounts"]) >= 2)
        self.assertTrue(response.content["account_count"] >= 2)

    def test_get_accounts_with_pagination(self):
        paginations = [{"page": 1, "page_size": 1},
                       {"page": 2, "page_size": 1}]

        for pagination in paginations:
            with self.subTest(pagination = pagination):
                response = TestAccounts.admin_client.get_accounts(pagination)

                self.assertEqual(response.status_code, 200)
                self.assertSchema(response.content, ACCOUNTS_SCHEMA)
                self.assertEqual(len(response.content["accounts"]), 1)
                self.assertTrue(response.content["account_count"] >= 2)

    def test_get_persons_bad_params(self):
        bad_params = {"page": "a", "page_size": "a"}
        self.badParamTests(bad_params, BaseClass.admin_client.get_persons)

    def test_method_not_allowed(self):
        self.methodNotAllowed("{}/accounts".format(BaseClass.admin_client.url),
                              ["post", "put", "delete", "patch"])
