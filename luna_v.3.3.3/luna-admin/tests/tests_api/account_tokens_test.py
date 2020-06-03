from base_class import BaseClass
from schemas import TOKENS_SCHEMA
from luna_admin.crutches_on_wheels.errors.errors import Error
from uuid import uuid4


class TestAccountTokens(BaseClass):

    def test_get_account(self):
        response = TestAccountTokens.admin_client.get_account_tokens(TestAccountTokens.employer.account_id)

        self.assertEqual(response.status_code, 200)
        self.assertSchema(response.content, TOKENS_SCHEMA)

    def test_get_non_exist_account(self):
        response = TestAccountTokens.admin_client.get_account_tokens(str(uuid4()))
        self.assertErrorRestAnswer(response, 404, Error.AccountNotFound)

    def test_method_not_allowed(self):
        self.methodNotAllowed("{}/accounts/{}/tokens".format(BaseClass.admin_client.url, str(uuid4())),
                              ["post", "put", "delete", "patch"])
