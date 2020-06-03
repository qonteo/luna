"""
Module realize a handler for work with lists from luna-faces
"""
from luna3.common.exceptions import LunaApiException
from tornado import gen
from typing import Generator

from app.handlers.base_handler import BaseHandler, BaseHandlerWithAuth
from common.api_clients import FACES_CLIENT
from common.query_validators import uuid4Getter, int01Getter
from crutches_on_wheels.errors.errors import Error


def getViewOfList(lunaList: dict) -> dict:
    """
    Convert luna list from luna-faces to luna-admin view

    Args:
        lunaList: luna list from luna-faces

    Returns:
        new view
    """
    return {"list_id": lunaList["list_id"], "account_id": lunaList["account_id"],
            "last_update_time": lunaList["last_update_time"],
            "count_object_in_list": lunaList["person_count"] if lunaList["type"] else lunaList["face_count"],
            "user_data": lunaList["user_data"],
            "type": lunaList["type"]}


class AccountListsHandler(BaseHandlerWithAuth):
    """
    Handler for lists.
    """
    @BaseHandlerWithAuth.requestExceptionWrap
    @gen.coroutine
    def get(self) -> Generator[None, None, None]:
        """
        Get lists with pagination.

        .. http:get:: /lists

            :query page: page count, default 1
            :query page_size: page size, default 10
            :query account_id: account id
            :query type: list type

            :reqheader Authorization: basic authorization

            **Example response**:



                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

                .. json:object:: list of luna lists
                    :showexample:

                    :property lists: lists
                    :proptype lists: _list_(:json:object:`luna_list`)
                    :property list_count: list count
                    :proptype list_count: integer

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: success
            :statuscode 400: Bad query parameters
            :statuscode 500: internal server error
        """
        page, pageSize = self.getPagination()
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        listType = self.getQueryParam("type", int01Getter)

        lists = yield FACES_CLIENT.getLists(listType=listType, page=page, pageSize=pageSize, raiseError=True,
                                            accountId=accountId, lunaRequestId=self.requestId)
        res = [getViewOfList(lunaList) for lunaList in lists.json["lists"]]
        return self.success(200, outputJson={"lists": res, "list_count": lists.json["count"]})


class AccountListHandler(BaseHandlerWithAuth):
    """
    Luna-faces list handler.
    """

    @BaseHandlerWithAuth.requestExceptionWrap
    @gen.coroutine
    def get(self, listId: str) -> Generator[None, None, None]:
        """
        Get list info.

        .. http:get:: /lists/{listId}

            :param listId: list id

            :reqheader Authorization: basic authorization

            **Example response**:



                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

            Output account will be represent in  :json:object:`luna_list`

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: list was gotten successfully.
            :statuscode 404: List not found
            :statuscode 500: internal server error
        """
        try:
            response = yield FACES_CLIENT.getList(listId=listId, raiseError=True, lunaRequestId=self.requestId)

            lunaList = response.json
            res = getViewOfList(lunaList)
            return self.success(200, outputJson=res)
        except LunaApiException as e:
            if e.statusCode == 404:
                return self.error(404, error=Error.AccountListNotFound)
            else:
                raise
