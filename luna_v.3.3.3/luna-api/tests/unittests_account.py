from crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase
from tests.functions import checkUUID4
from tests import luna_api_functions


def tokenInReply(tokens, tokenId):
    for token in tokens:
        if token["id"] == tokenId:
            return True
    return False


class TestAccount(TestBase):
    """
    Test action of account.
    """
    maxLengthTokenData = "x" * 128
    largeLengthTokenData = "x" * 129
    badTypeTokenData = 1
    badTokenId = "xxxxxxxx-xxxx-xxxx-xxxx-241e0ab1f0da"

    def setUp(self):
        self.createAccount()

    def assert404(self, response):
        self.assertEqual(404, response.statusCode)
        self.assertDictEqual({"error_code": Error.PageNotFoundError.errorCode, "detail": "Page not found"},
                             response.body)

    # region TestAccount
    def test_account_get_account_info(self):
        """
        .. test:: test_account_get_account_info

            :resources: "/account"
            :description: success getting correct account info.
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.getAccountData()
        self.assertEqual(replyInfo.statusCode, 200)
        self.assertTrue("email" in replyInfo.body)
        self.assertEqual(self.email, replyInfo.body["email"])
        self.assertTrue("suspended" in replyInfo.body)
        self.assertEqual(False, replyInfo.body["suspended"])
        self.assertTrue("organization_name" in replyInfo.body)
        self.assertEqual(self.organization_name, replyInfo.body["organization_name"])

    def test_account_get_account_info_with_bad_password(self):
        """
        .. test:: test_account_get_account_info_with_bad_password

            :resources: "/account"
            :description: try get account info with wrong password.
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.getAccountData(luna_api_functions.TEST_EMAIL, 'bad_password')
        self.assertErrorRestAnswer(replyInfo, 401, Error.AccountNotFound)

    def test_account_get_account_info_with_bad_email(self):
        """

        .. test:: test_account_get_account_info_with_bad_email

            :resources: "/account"
            :description: try get account info with wrong email.
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.getAccountData('bad_email', luna_api_functions.TEST_PASSWORD)
        self.assertErrorRestAnswer(replyInfo, 401, Error.AccountNotFound)

    def test_account_get_account_info_with_empty_email_and_password(self):
        """
        .. test:: test_account_get_account_info_with_empty_email_and_password

            :resources: "/account"
            :description: try get account info with empty e-mail and password.
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.getAccountData(email='', password='')
        self.assertErrorRestAnswer(replyInfo, 401, Error.AccountNotFound)

    def test_token_get_account_info_with_bad_basic(self):
        """
        .. test:: test_token_get_account_info_with_bad_basic

            :resources: "/account'
            :description: try getting account info with bad format basic auth
            :LIS: No
            :tag: Account actions
        """

        replyInfo = luna_api_functions.manualRequest('/account', 'GET',
                                                     authData=luna_api_functions.createBadBase64BasicAuthHeader())
        self.assertErrorRestAnswer(replyInfo, 401, Error.BadHeaderAuth, msgFormat=["Authorization"])

    # endregion Account

    # region TestAccountTokens
    # region POST
    def test_token_create_token(self):
        """
        .. test:: test_token_create_token

            :resources: "/account/tokens"
            :description: success creating token without data.
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.createToken()
        self.assertToken(replyInfo)

    def test_token_create_token_with_data(self):
        """
        .. test:: test_token_create_token_with_data

            :resources: "/account/tokens"
            :description: success creating token with data.
            :LIS: No
            :tag: Account actions
        """
        data = "some token data"
        replyInfo = luna_api_functions.createToken(tokenData=data)
        self.assertToken(replyInfo)
        tokenId = replyInfo.body['token']
        self.assertTokenData(tokenId, data)

    def test_token_create_token_with_maximum_data_length(self):
        """
        .. test:: test_token_create_token_with_maximum_data_length

            :resources: "/account/tokens"
            :description: try creating token with maximum allowed length of token_data (=128)
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.createToken(tokenData=self.maxLengthTokenData)
        self.assertToken(replyInfo)

    def test_token_create_token_with_large_data(self):
        """
        .. test:: test_token_create_token_with_large_data

            :resources: "/account/tokens"
            :description: try creating token with bad length of token_data (>128)
            :LIS: No
            :tag: Account actions
        """
        tokens_id_count_before = self.getTokensIdCount()
        replyInfo = luna_api_functions.createToken(tokenData=self.largeLengthTokenData)
        self.assertErrorRestAnswer(replyInfo, 400, Error.BigUserData)
        self.assertTokensCountNotChanged(tokens_id_count_before, 'POST')

    def test_token_create_token_with_bad_type_value(self):
        """
        .. test:: test_token_create_token_with_bad_type_value

            :resources: "/account/tokens"
            :description: try creating token with bad type of user data (int)
            :LIS: No
            :tag: Account actions
        """
        tokens_id_count_before = self.getTokensIdCount()
        replyInfo = luna_api_functions.createToken(tokenData=self.badTypeTokenData)
        self.assertErrorRestAnswer(replyInfo, 400, Error.BadTypeOfFieldInJSON, msgFormat=['token_data', 'string'])
        self.assertTokensCountNotChanged(tokens_id_count_before, 'POST')
    # endregion POST

    # region GET
    def test_token_get_list_tokens(self):
        """
        .. test:: test_token_get_list_tokens

            :resources: "/account/tokens"
            :description: success getting account tokens
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.createToken()
        token = replyInfo.body["token"]
        replyInfo = luna_api_functions.getTokens()
        self.assertEqual(replyInfo.statusCode, 200)
        self.assertTrue('tokens' in replyInfo.body)
        for token in replyInfo.body['tokens']:
            self.assertTrue(checkUUID4(token["id"]))

    def test_token_get_list_tokens_with_pagination(self):
        """
        .. test:: test_token_get_list_tokens_with_pagination

            :resources: "/account/tokens"
            :description: success getting account tokens with pagination
            :LIS: No
            :tag: Account actions
        """
        for _ in range(4):
            luna_api_functions.createToken("test_token_get_list_tokens_with_pagination")

        replyInfo1 = luna_api_functions.getTokens(pageSize=2, page=1)
        self.assertEqual(2, len(replyInfo1.body["tokens"]))
        replyInfo2 = luna_api_functions.getTokens(pageSize=2, page=2)
        self.assertEqual(2, len(replyInfo2.body["tokens"]))
        self.assertTrue(replyInfo2.body["tokens"][0]["id"] != replyInfo1.body["tokens"][0]["id"])

    # endregion GET

    # region DELETE
    def test_token_delete_tokens(self):
        """
        .. test:: test_token_delete_tokens

            :resources: "/account/tokens"
            :description: success removing tokens.
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.createToken()
        token1 = replyInfo.body["token"]
        replyInfo = luna_api_functions.createToken()
        token2 = replyInfo.body["token"]
        replyInfo = luna_api_functions.deleteTokens(tokens=[token1, token2])
        self.assertEqual(replyInfo.statusCode, 204)
        for token in (token1, token2):
            reply = luna_api_functions.getLists({"token": token})
            self.assertEqual(401, reply.statusCode)

    def test_token_delete_token_empty_json(self):
        """
        .. test:: test_token_delete_token_empty_json

            :resources: "/account/tokens"
            :description: try remove  tokens without json in request
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.manualRequest('/account/tokens', 'DELETE')
        self.assertErrorRestAnswer(replyInfo, 400, Error.EmptyJson)

    def test_token_delete_token_with_bad_key_in_json(self):
        """
        .. test:: test_token_delete_token_with_bad_key_in_json

            :resources: "/account/tokens"
            :description: try remove  tokens with wrong key in json("token" instead "tokens")
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.createToken(self.email, self.password)
        token1 = replyInfo.body["token"]
        payload = {"token": [token1]}
        tokensCountBefore = self.getTokensIdCount()
        replyInfo = luna_api_functions.manualRequest('/account/tokens', 'DELETE', payload)
        self.assertErrorRestAnswer(replyInfo, 400, Error.FieldNotInJSON, msgFormat=["tokens"])
        self.assertTokensCountNotChanged(tokensCountBefore, 'DELETE')

    def test_token_delete_token_with_bad_type_value_in_json(self):
        """
        .. test:: test_token_delete_token_with_bad_type_value_in_json

            :resources: "/account/tokens"
            :description: try remove tokens with wrong type of value in json(token id instead list of tokens)
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.createToken()
        token1 = replyInfo.body["token"]
        tokensCountBefore = self.getTokensIdCount()
        replyInfo = luna_api_functions.deleteTokens(tokens=token1)
        self.assertErrorRestAnswer(replyInfo, 400, Error.BadTypeOfFieldInJSON, msgFormat=["tokens", "list"])
        self.assertTokensCountNotChanged(tokensCountBefore, 'DELETE')

    def test_token_delete_token_with_invalid_token_id(self):
        """
        .. test:: test_token_delete_token_with_invalid_token_id

            :resources: "/account/tokens"
            :description: try remove tokens with invalid token id in json value
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.createToken()
        token1 = replyInfo.body["token"]
        payload = [token1, self.badTokenId]
        replyInfo = luna_api_functions.deleteTokens(tokens=payload)
        # TODO replace return status code and error message by more convenient
        self.assertErrorRestAnswer(replyInfo, 400, Error.BadFormatUUID)

    # endregion DELETE
    # endregion TestAccountTokens

    # region TestAccountTokensTokenId
    # region PATCH
    def test_token_patch_token(self):
        """
        .. test:: test_token_patch_token

            :resources: "/account/tokens/\{token_id\}'
            :description: success patching token data.
            :LIS: No
            :tag: Account actions
        """
        data = "some token data"
        replyInfo = luna_api_functions.createToken(tokenData=data)
        self.assertToken(replyInfo)
        tokenId = replyInfo.body['token']
        self.assertTokenData(tokenId, data)
        newData = "new some token data"
        replyInfo = luna_api_functions.patchTokenData(tokenId=tokenId, tokenData=newData)
        self.assertEqual(replyInfo.statusCode, 204)
        self.assertTokenData(tokenId, newData)

    def test_token_patch_token_with_maximum_data_length(self):
        """
        .. test:: test_token_patch_token_with_maximum_data_length

            :resources: "/account/tokens/\{token_id\}'
            :description: try patching token data with maximum data length (=128).
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.createToken("")
        self.assertToken(replyInfo)
        tokenId = replyInfo.body['token']
        replyInfo = luna_api_functions.patchTokenData(tokenId=tokenId, tokenData=self.maxLengthTokenData)
        self.assertEqual(replyInfo.statusCode, 204)
        self.assertTokenData(tokenId, self.maxLengthTokenData)

    def test_token_patch_token_with_large_data_length(self):
        """
        .. test:: test_token_patch_token_with_large_data_length

            :resources: "/account/tokens/\{token_id\}'
            :description: try patching token data with maximum data length (>128).
            :LIS: No
            :tag: Account actions
        """
        source_data = "data before patching"
        replyInfo = luna_api_functions.createToken(tokenData=source_data)
        self.assertToken(replyInfo)
        tokenId = replyInfo.body['token']
        replyInfo = luna_api_functions.patchTokenData(tokenId=tokenId, tokenData=self.largeLengthTokenData)
        self.assertErrorRestAnswer(replyInfo, 400, Error.BigUserData)
        self.assertTokenData(tokenId, source_data)

    def test_token_patch_token_with_invalid_token_id(self):
        """
        .. test:: test_token_patch_token_with_invalid_token_id

            :resources: "/account/tokens/\{token_id\}'
            :description: try patching token data with invalid token id.
            :LIS: No
            :tag: Account actions
        """
        newData = "new some token data"
        replyInfo = luna_api_functions.patchTokenData(tokenId=self.badTokenId, tokenData=newData)
        self.assert404(replyInfo)

    # todo: json is not empty for default(luna_api.py)
    def test_token_patch_token_with_empty_string_as_json(self):
        """
        .. test:: test_token_patch_token_with_empty_string_as_json

            :resources: "/account/tokens/\{token_id\}'
            :description: try patching token data with empty string as json.
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.createToken(self.email, self.password, "")
        self.assertToken(replyInfo)
        tokenId = replyInfo.body['token']
        replyInfo = luna_api_functions.manualRequest('/account/tokens/' + tokenId, 'PATCH', '')
        self.assertErrorRestAnswer(replyInfo, 400, Error.FieldNotInJSON, msgFormat=["token_data"])

    def test_token_patch_token_with_bad_json_key(self):
        """
        .. test:: test_token_patch_token_with_bad_json_key

            :resources: "/account/tokens/\{token_id\}'
            :description: try patching token with wrong key in json ("tokens_data" instead "token_data")
            :LIS: No
            :tag: Account actions
        """
        source_data = "data before patching"
        replyInfo = luna_api_functions.createToken(self.email, self.password, source_data)
        self.assertToken(replyInfo)
        tokenId = replyInfo.body['token']
        replyInfo = luna_api_functions.manualRequest('/account/tokens/' + tokenId, 'PATCH', '')
        self.assertErrorRestAnswer(replyInfo, 400, Error.FieldNotInJSON, msgFormat=["token_data"])
        self.assertTokenData(tokenId, source_data)

    def test_token_patch_token_with_invalid_json_type(self):
        """
        .. test:: test_token_patch_token_with_invalid_json_type

            :resources: "/account/tokens/\{token_id\}'
            :description: try patching token data with 1(int) as json.
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.createToken(self.email, self.password, "")
        self.assertToken(replyInfo)
        tokenId = replyInfo.body['token']
        replyInfo = luna_api_functions.manualRequest('/account/tokens/' + tokenId, 'PATCH', self.badTypeTokenData)
        self.assertErrorRestAnswer(replyInfo, 400, Error.RequestNotContainsJson)

    # endregion PATCH

    # region DELETE
    def test_token_delete_token_by_id(self):
        """
        .. test:: test_token_delete_token_by_id

            :resources: "/account/tokens/\{token_id\}'
            :description: success removing token by id.
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.createToken()
        token1 = replyInfo.body["token"]
        replyInfo = luna_api_functions.createToken()
        token2 = replyInfo.body["token"]
        replyInfo = luna_api_functions.deleteToken(tokenId=token1)
        self.assertEqual(replyInfo.statusCode, 204)
        reply = luna_api_functions.getLists({"token": token2})
        self.assertEqual(200, reply.statusCode)
        reply = luna_api_functions.getLists({"token": token1})
        self.assertEqual(401, reply.statusCode)

    def test_token_delete_token_by_invalid_id(self):
        """
        .. test:: test_token_delete_token_by_invalid_id

            :resources: "/account/tokens/\{token_id\}'
            :description: success removing token by invalid id.
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.deleteToken(tokenId=self.badTokenId)
        self.assert404(replyInfo)

    # endregion DELETE

    # region GET
    def test_token_get_token_by_id(self):
        """
        .. test:: test_token_get_token_by_id

            :resources: "/account/tokens/\{token_id\}'
            :description: success getting token by id.
            :LIS: No
            :tag: Account actions
        """
        data = "some token data"
        replyInfo = luna_api_functions.createToken(tokenData=data)
        self.assertToken(replyInfo)
        tokenId = replyInfo.body['token']
        replyInfo = luna_api_functions.getToken(tokenId=tokenId)
        self.assertTrue("token_data" in replyInfo.body)
        self.assertEqual(data, replyInfo.body["token_data"])

    def test_token_get_token_by_invalid_id(self):
        """
        .. test:: test_token_get_token_by_invalid_id

            :resources: "/account/tokens/\{token_id\}'
            :description: try getting token by invalid id.
            :LIS: No
            :tag: Account actions
        """
        replyInfo = luna_api_functions.getToken(tokenId=self.badTokenId)
        self.assert404(replyInfo)

    # endregion GET
    # endregion TestAccountTokensTokenId

    def getTokensIdCount(self):
        replyInfo = luna_api_functions.getTokens()
        return replyInfo.body['count']

    def assertTokensCountNotChanged(self, tokensCountBefore, method_name):
        tokensCountAfter = self.getTokensIdCount()
        self.assertEqual(tokensCountBefore, tokensCountAfter, msg="Number of token ids has changed after \
            invalid {0}: before={1}, after={2}".format(method_name, tokensCountBefore, tokensCountAfter))

    def assertTokenData(self, tokenId, tokenData):
        replyInfo = luna_api_functions.getToken(tokenId=tokenId)
        self.assertEqual(replyInfo.body["token_data"], tokenData)

    def assertToken(self, replyInfo):
        self.assertEqual(replyInfo.statusCode, 201)
        self.assertTrue('token' in replyInfo.body)
        self.assertTrue(checkUUID4(replyInfo.body['token']))
