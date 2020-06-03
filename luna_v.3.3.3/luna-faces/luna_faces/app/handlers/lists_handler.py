from app.handlers.base_handler import BaseRequestHandler
from app.handlers.query_validators import uuid4Getter, int01Getter
from app.handlers.shemas import CREATE_LIST_SCHEMAS, DELETE_LISTS_SCHEMA, GET_LISTS_WITH_KEYS_SCHEMA
from app.version import VERSION
from crutches_on_wheels.errors.errors import Error


class ListsHandler(BaseRequestHandler):
    """
    Handler for work with lists
    """

    @BaseRequestHandler.requestExceptionWrap
    def get(self):
        """
        Get lists by id.

        Resource is reached by address '/lists'

        .. http:get:: /lists

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id
            :query user_data: user data
            :query page: page count, default 1
            :query page_size: page size, default 10

            .. sourcecode:: http

                GET /lists HTTP/1.1


            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json


            .. json:object:: luna_lists
                :showexample:

                :property lists: lists
                :proptype lists: _list_(:json:object:`luna_list`)
                :property count: list count
                :proptype count: integer

            :statuscode 200: Ok
            :statuscode 500: internal server error
        """

        page, pageSize = self.getPagination()
        accountId = self.getQueryParam("account_id", uuid4Getter)
        userData = self.getQueryParam("user_data")
        listType = self.getQueryParam("type", int01Getter)
        listCount, lists = self.dbContext.getLists(accountId=accountId, userData=userData,
                                                   page=page, pageSize=pageSize, listType=listType)
        self.success(200, outputJson={"count": listCount, "lists": lists})

    @BaseRequestHandler.requestExceptionWrap
    def options(self):
        """
        Get lists of faces with last link id and last unlink id.

        Resource is reached by address '/lists'

        .. http:options:: /lists

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                OPTIONS /lists HTTP/1.1


            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json


            .. json:object:: luna_lists_with_keys
                :showexample:

                :property lists: lists
                :proptype lists: _list(:json:object:`_luna_list_with_keys`)

            :statuscode 200: Ok
            :statuscode 500: internal server error
        """

        data = self.getInputJson()
        self.validateJson(data, GET_LISTS_WITH_KEYS_SCHEMA)
        lists = self.dbContext.getListsWithKeys(data["list_ids"])
        self.success(200, outputJson={"lists": lists})

    @BaseRequestHandler.requestExceptionWrap
    def post(self):
        """
        Resource is reached by address '/lists'

        .. http:post:: /lists

            Request to create list.

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                POST /lists HTTP/1.1
                Accept: application/json

            .. json:object:: luna_create_lists
                :showexample:

                :property account_id: id of account, required
                :proptype account_id: uuid4
                :property user_data: list information (case sensitive)
                :proptype user_data: user_name


            .. sourcecode:: http

                HTTP/1.1 201 Created
                Content-Type: application/json
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Location: /lists/{face_id}

                .. json:object:: list_id
                    :showexample:

                    :property list_id: id of created list
                    :proptype list_id: uuid4

            Error message is returned on format :json:object:`server_error`.

            :statuscode 201: list successfully create
            :statuscode 400: field *user_data* is too large
            :statuscode 400: field *user_data* has wrong type, *string* type is required
            :statuscode 500: internal server error
        """

        data = self.getInputJson()
        self.validateJson(data, CREATE_LIST_SCHEMAS)
        faceId = self.dbContext.createList(**data)
        self.add_header("Location", "/{}/lists/{}".format(VERSION["Version"]["api"], faceId))
        self.success(201, outputJson={"list_id": faceId})

    @BaseRequestHandler.requestExceptionWrap
    def delete(self):
        """
        Delete list

        Request to remove lists.

        Resource is reached by address '/lists'

        .. http:delete:: /lists

            :reqheader LUNA-Request-Id: request id
            :query account_id: account id, this parameter determinate, that action must be done with only with objects
                                  of this account.

            .. sourcecode:: http

                DELETE /lists/ HTTP/1.1

            **Example response**:


            .. sourcecode:: http

                HTTP/1.1 204
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f

            :statuscode 204: Ok
            :statuscode 400: one or more lists not found
            :statuscode 500: internal server error
        """
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)
        data = self.getInputJson()
        self.validateJson(data, DELETE_LISTS_SCHEMA)
        if not self.dbContext.isListsExist(data["list_ids"], accountId):
            return self.error(400, error=Error.ListsNotFound)
        self.dbContext.deleteLists(data["list_ids"])
        self.success(204)
