from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import uuid4Getter
from app.handlers.shemas import PATCH_LIST_USER_SCHEMA
from crutches_on_wheels.errors.errors import Error


class ListHandler(BaseRequestHandler):
    """
    Handler for work with list
    """

    @BaseRequestHandler.requestExceptionWrap
    def prepare(self):
        """
        Checking exist list or not.

        If face is not exist, will call self.error with error Error.FaceNotFound
        """
        if self.request.method == "GET":
            return
        listId = self.request.uri.split("/")[-1].split("?")[0]
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        if not self.dbContext.isListExist(listId, accountId):
            self.error(404, error=Error.ListNotFound)

    @BaseRequestHandler.requestExceptionWrap
    def head(self, listId: str):
        """
        Check list existence by id.

        Resource is reached by address '/lists/{listId}'

        .. http:get:: /lists/{listId}

            :param listId: list id

            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                               of this account.
            :query page: page count, default 1
            :query page_size: page size, default 10

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                HEAD /lists/{listId} HTTP/1.1
                Accept: application/json


            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json

            :statuscode 200: Ok
            :statuscode 404: list not found
            :statuscode 500: internal server error
        """
        return self.success(200)

    @BaseRequestHandler.requestExceptionWrap
    def get(self, listId: str):
        """
        Get list by id.

        Resource is reached by address '/lists/{listId}'

        .. http:get:: /lists/{listId}

            :param listId: list id

            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                               of this account.
            :query page: page count, default 1
            :query page_size: page size, default 10

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                GET /lists/{listId} HTTP/1.1
                Accept: application/json


            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 200
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json


            Output faces will be represent in  :json:object:`luna_list`.

            :statuscode 200: Ok
            :statuscode 404: list not found
            :statuscode 500: internal server error
        """
        page, pageSize = self.getPagination(minPageSize=0)
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        listCount, lists = self.dbContext.getLists(listIds=[listId], accountId=accountId)
        if not listCount:
            return self.error(404, error=Error.ListNotFound)
        if lists[0]["type"] == 0:
            _, faces = self.dbContext.getFaces(page=page, pageSize=pageSize, listId=listId, calculateFaceCount=0)
            res = {"faces": faces}
        else:
            _, persons = self.dbContext.getPersons(page=page, pageSize=pageSize, listId=listId, calculateFaceCount=0)
            res = {"persons": persons}
        res.update(lists[0])
        return self.success(200, outputJson=res)

    @BaseRequestHandler.requestExceptionWrap
    def patch(self, listId: str):
        """
        Update user date for list
        :param listId: list id

        Resource is reached by address '/lists/{listId}'

        .. http:patch:: /lists/{listId}

            :param listId: list id

            :reqheader LUNA-Request-Id: request id
            :reqheader Content-Type: application/json

            :optparam account_id: account id, this parameter determinate, that action must be done with only with objects
                                  of this account.

            .. sourcecode:: http

                PATCH /lists/{listId} HTTP/1.1
                Content-Type: application/json

            .. json:object:: luna_patch_lists
                :showexample:

                :property user_data: list information
                :proptype user_data: user_name

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f

            :statuscode 204: Ok
            :statuscode 404: list not found
            :statuscode 500: internal server error
        """
        data = self.getInputJson()
        self.validateJson(data, PATCH_LIST_USER_SCHEMA)
        self.dbContext.updateListUserData(listId, data["user_data"])
        self.success(204)

    @BaseRequestHandler.requestExceptionWrap
    def delete(self, listId: str):
        """
        Delete list

        Request to remove the list.

        :param listId: list id

        Resource is reached by address '/lists/{listId}'

        .. http:delete:: /lists/{listId}

            :param listId: list id

            :optparam account_id: account id, this parameter determinate, that action must be done with only with objects
                                  of this account.

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                DELETE /lists/{listId} HTTP/1.1

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f

            :statuscode 204: Ok
            :statuscode 404: list not found
            :statuscode 500: internal server error
        """
        self.dbContext.deleteLists([listId])
        self.success(204)
