from luna3.common.exceptions import LunaApiException
from app.handlers.base_handler import BaseHandlerWithAuth
from common.query_validators import isUUID4
from typing import Generator
from tornado import gen


class SearchHandler(BaseHandlerWithAuth):
    """
    Search objects handler.
    """

    @property
    def MapColumnGetter(self) -> dict:
        """
        Returns MAP_COLUMN_GETTER
        """
        return {"account_list_id": {"getter": self.objectGetters.getListInfo, "name": "account_list"},
                "account_id": {"getter": self.objectGetters.getAccountInfo, "name": "account"},
                "token_id": {
                    "getter": lambda x: self.objectGetters.getAccountInfo(self.dbApiContext.getAccountIdByToken(x)),
                    "name": "account"},
                "photo_id": {"getter": self.objectGetters.getFaceInfo, "name": "face"},
                "person_id": {"getter": self.objectGetters.getPersonInfo, "name": "person"}
                }

    @gen.coroutine
    def getElementByIdAndColumn(self, column: str, elementId: str) -> Generator[None, None, dict]:
        """
        Get element by id from column.

        Args:
            column: column name
            elementId: element id

        Returns:
            dict with element and element type
        """
        data = yield self.MapColumnGetter[column]["getter"](elementId)
        return {"data": data, "type": self.MapColumnGetter[column]["name"]}

    @BaseHandlerWithAuth.requestExceptionWrap
    @gen.coroutine
    def get(self):
        """
        Search element by id or email.

        .. http:get:: /search

            :query q: uuid or email

            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

                .. json:object:: search result
                    :showexample:

                    :property data: dict with object (:json:object:`luna_list`, :json:object:`account`,
                                    :json:object:`luna_person`, face of None)
                    :proptype data: _enum_(:json:object:`luna_list`)_(:json:object:`account`)_(:json:object:`luna_person`)
                    :property type: type of date
                    :proptype type: _enum_(person)_(account)_(face)_(list)_(null)


            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: success
            :statuscode 400: Bad query parameters
            :statuscode 500: internal server error
        """
        searchParam = self.get_query_argument('q', None)

        if isUUID4(searchParam):
            for column in self.MapColumnGetter:
                try:
                    element = yield self.getElementByIdAndColumn(column, searchParam)
                except LunaApiException as e:
                    if e.statusCode == 404:
                        continue
                    raise
                if element["data"] is not None:
                    return self.success(200, outputJson=element)
            return self.success(200, outputJson={"data": None, "type": None})
        else:
            account_id = self.dbApiContext.getAccountIdByEmail(searchParam)
            if account_id is None:
                return self.success(200, outputJson={"data": None, "type": None})
            account = yield self.objectGetters.getAccountInfo(account_id)
            return self.success(200, outputJson={"data": account, "type": "account"})
