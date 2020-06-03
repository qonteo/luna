from app.handlers.base_handler import BaseHandlerWithAuth
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.errors.errors import Error


class AccountTokensHandler(BaseHandlerWithAuth):

    """
    Handler of account tokens
    """
    @BaseHandlerWithAuth.requestExceptionWrap
    def get(self, account_id: str) -> None:
        """
        Get tokens of account with pagination.

        .. http:get:: /accounts/{account_id}

            :param account_id: account id

            :query page: page count, default 1
            :query page_size: page size, default 10

            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

                .. json:object:: list of account tokens
                    :showexample:

                    :property tokens: tokens
                    :proptype tokens: _list_(:json:object:`auth_token`)
                    :property token_count: token count
                    :proptype token_count: integer

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: success
            :statuscode 400: Bad query parameters
            :statuscode 500: internal server error
        """
        if self.dbApiContext.getAccount(account_id) is None:
            raise VLException(Error.AccountNotFound, 404, isCriticalError=False)
        page, pageSize = self.getPagination()
        countToken = self.dbApiContext.getCountTokens(account_id)
        tokens = self.dbApiContext.getAccountTokens(account_id, page, pageSize)

        return self.success(200,
                            outputJson={"tokens": [{"token_id": token[0], "token_data": token[1]} for token in tokens],
                                        "token_count": countToken})
