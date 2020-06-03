"""
Module realize handlers for work with an account.
"""
from tornado import gen
from typing import Generator
from app.handlers.base_handler import BaseHandlerWithAuth
from common.query_validators import int01Getter
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.errors.errors import Error


class AccountHandler(BaseHandlerWithAuth):
    """
    Handler for work with an account.
    """

    @BaseHandlerWithAuth.requestExceptionWrap
    def patch(self, account_id: str) -> None:
        """
        Request for block or unblock account.

        .. http:patch:: /accounts/{account_id}

            :param account_id: account id

            :query status: 0 or 1 (disable or activate)

            :reqheader Authorization: basic authorization

            **Example response**:



                .. sourcecode:: http

                    HTTP/1.1 204 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

            Message error is returned in format :json:object:`server_error`.

            :statuscode 204: account was patched successfully.
            :statuscode 404: Account not found
            :statuscode 500: internal server error

        Raises:
            VLException(Error.AccountNotFound, 404, isCriticalError=False): if account not found
        """
        if self.dbApiContext.getAccount(account_id) is None:
            raise VLException(Error.AccountNotFound, 404, isCriticalError=False)

        state = self.getQueryParam("status", lambda x: bool(int01Getter(x)))
        self.dbApiContext.blockAccount(account_id, state)
        self.success(204)

    @BaseHandlerWithAuth.requestExceptionWrap
    @gen.coroutine
    def get(self, account_id: str) -> Generator[None, None, None]:
        """
        Get account info.

        .. http:get:: /accounts/{account_id}

            :param account_id: account id


            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

            Output account will be represent in  :json:object:`account`

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: account was gotten successfully.
            :statuscode 404: Account not found
            :statuscode 500: internal server error

        Raises:
            VLException(Error.AccountNotFound, 404, isCriticalError=False): if account not found

        """
        if self.dbApiContext.getAccount(account_id) is None:
            raise VLException(Error.AccountNotFound, 404, isCriticalError=False)
        acc = yield self.objectGetters.getAccountInfo(account_id)
        return self.success(200, outputJson=acc)
