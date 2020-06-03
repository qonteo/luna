"""
Module realize a handler for work with several accounts
"""
from tornado import web

from app.handlers.base_handler import BaseHandlerWithAuth


class AccountsHandler(BaseHandlerWithAuth):
    """
    Handler for work with several accounts
    """
    @BaseHandlerWithAuth.requestExceptionWrap
    def get(self) -> None:
        """
        Get accounts with  pagination.

        .. http:get:: /accounts

            :query page: page count, default 1
            :query page_size: page size, default 10


            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

                .. json:object:: list of faces
                    :showexample:

                    :property accounts: accounts
                    :proptype accounts: _list_(:json:object:`account`)
                    :property account_count: account count
                    :proptype account_count: integer

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: success
            :statuscode 400: Bad query parameters
            :statuscode 500: internal server error
        """
        page, pageSize = self.getPagination()

        accounts = self.dbApiContext.getAccounts(page, pageSize)
        accounts = [{"account_id": account[0], "organization_name": account[1],
                     "status": int(account[3]), "email": account[2]} for account in accounts]
        accountCount = self.dbApiContext.getCountAccounts()

        return self.success(200, outputJson={"accounts": accounts, "account_count": accountCount})
