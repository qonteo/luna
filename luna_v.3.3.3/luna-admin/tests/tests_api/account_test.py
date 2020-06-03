from base_class import BaseClass
from schemas import ACCOUNT_FULL
from resources.resources import warp, no_faces
from luna_admin.crutches_on_wheels.errors.errors import Error
from uuid import uuid4


class TestAccount(BaseClass):

    def test_get_account(self):
        response = TestAccount.admin_client.get_account(TestAccount.employer.account_id)

        self.assertEqual(response.status_code, 200)
        self.assertSchema(response.content, ACCOUNT_FULL)

    def test_get_non_exist_account(self):
        response = TestAccount.admin_client.get_account(str(uuid4()))
        self.assertErrorRestAnswer(response, 404, Error.AccountNotFound)

    def test_block_unlock_account(self):
        response = TestAccount.admin_client.patch_account(TestAccount.employer.account_id, 0)

        self.assertEqual(response.status_code, 204)
        response = TestAccount.employer.api_client.getTokens()
        self.assertEqual(response.statusCode, 403)
        response = TestAccount.employer.api_client.extractDescriptors(
            filename=no_faces)
        self.assertEqual(response.statusCode, 403)

        response = TestAccount.admin_client.patch_account(TestAccount.employer.account_id, 1)
        self.assertEqual(response.status_code, 204)
        response = TestAccount.employer.api_client.getTokens()
        self.assertEqual(response.statusCode, 200)
        response = TestAccount.employer.api_client.extractDescriptors(
            filename=warp, warpedImage=True)
        self.assertEqual(response.statusCode, 201)

    def test_method_not_allowed(self):
        self.methodNotAllowed("{}/accounts/{}".format(BaseClass.admin_client.url, str(uuid4())),
                              ["post", "put", "delete"])
