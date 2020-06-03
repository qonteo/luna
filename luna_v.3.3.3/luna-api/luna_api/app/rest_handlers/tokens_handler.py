from tornado import web, escape

from app.rest_handlers.account_handler import AccountHandlerActive
from crutches_on_wheels.errors.errors import Error

from crutches_on_wheels.handlers.query_getters import isUUID4


class TokensHandler(AccountHandlerActive):
    """
    Handler to operate with account tokens. To operate with them, you should authorize into account and account must be
    active.
    """

    @web.asynchronous
    @AccountHandlerActive.requestExceptionWrap
    def get(self):
        """
        Resource to get all account tokens

        .. http:get:: /account/tokens

            :optparam page: A number of page. Minimum 1, default 1.
            :optparam page_size: Number of tokens of the same type on page.  Minimum 1, maximum 100, default 10.

            :reqheader Authorization: basic authorization

            :reqheader LUNA-Request-Id: request id

            **Example response**:

            .. sourcecode:: http

               HTTP/1.1 200 Ok
               Vary: Accept
               Content-Type: application/json
               LUNA-Request-Id: 1516179740,c06887a2

            .. json:object:: tokens
               :showexample:

               :property tokens: token list with token_data
               :proptype tokens: _list_(:json:object:`token_data`)
               :property count: number of tokens
               :proptype count: int

            Error message is returned in format  :json:object:`server_error`.
            
            :statuscode 500: internal server error
        """
        page, pageSize = self.getPagination()
        tokensRes = self.dbContext.getAccountTokens(self.accountId, page, pageSize)
        tokenCount = self.dbContext.getAccountTokenCount(self.accountId)
        self.success(200, outputJson={"tokens": [{"id": token[0], "token_data": token[1]}
                                                 for token in tokensRes], "count": tokenCount})

    @web.asynchronous
    @AccountHandlerActive.requestExceptionWrap
    def post(self):
        """
        Request for creation of new token for the account

        .. http:post:: /account/tokens

            :reqheader Authorization: basic authorization

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                POST /storage/tokens HTTP/1.1
                Accept: application/json

            Json to attach token data must be in format :json:object:`token_data`.

            **Example response**:

            .. sourcecode:: http

               HTTP/1.1 201 Ok
               Vary: Accept
               Content-Type: application/json
               LUNA-Request-Id: 1516179740,c06887a2

            .. json:object:: token
               :showexample:

               :property token: new token id
               :proptype token: uuid4

            Error message is returned in format :json:object:`server_error`.
                           
            :statuscode 400: field *token_data* is too large
            :statuscode 400: field *token_data* has wrong type, *string* field is required
            :statuscode 500: internal server error
        """
        info = self.getInfoFromRequest("token_data")

        if type(info) != str:
            error = Error.formatError(Error.BadTypeOfFieldInJSON, 'token_data', 'string')
            return self.error(400, error)
        if len(info) > 128:
            return self.error(400, Error.BigUserData)

        tokenRes = self.dbContext.createAccountToken(self.accountId, info)
        self.success(201, outputJson={"token": tokenRes})

    @web.asynchronous
    @AccountHandlerActive.requestExceptionWrap
    def delete(self):
        """
        Request to delete the list of account tokens

        .. http:delete:: /account/tokens

            **Example request**:

            :reqheader Authorization: basic authorization

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                POST /account/tokens HTTP/1.1
                Accept: application/json

            .. json:object:: json to delete tokens
                :showexample:

                :property tokens: tokens for deletion
                :proptype tokens: _list_(uuid4)

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204 Ok
                Vary: Accept
                LUNA-Request-Id: 1516179740,c06887a2

            Error message is returned in format :json:object:`server_error`.
            
            :statuscode 400: no json in request
            :statuscode 400: no *tokens* field in json
            :statuscode 400: *tokens* field is not a list
            :statuscode 500: internal server error
        """
        reqJson = self.getInputJson()

        if reqJson is None:
            return self.error(400, Error.EmptyJson)
        if not ("tokens" in reqJson):
            error = Error.formatError(Error.FieldNotInJSON, 'tokens')
            return self.error(400, error)
        tokens = reqJson["tokens"]
        if type(tokens) != list:
            error = Error.formatError(Error.BadTypeOfFieldInJSON, 'tokens', 'list')
            return self.error(400, error)
        for token in tokens:
            resCheckUUID = isUUID4(token)
            if not resCheckUUID:
                return self.error(400, Error.BadFormatUUID)
        self.dbContext.removeTokens(tokens, self.accountId)
        self.success(204)
