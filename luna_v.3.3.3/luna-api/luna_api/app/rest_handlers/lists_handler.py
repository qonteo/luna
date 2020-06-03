import tornado
from tornado import web, escape, gen

from app import functions
from app.rest_handlers.storage_handlers import StorageHandler
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.handlers.query_getters import isUUID4


@gen.coroutine
def deleteLists(lists, accountId, dbContext, lunaContext):
    """
    Delete account list.

    :param lunaContext: context to Luna Core
    :param dbContext: context to postgres
    :param lists: account lists
    :param accountId: account id
    :return: deletion result is returned from postgres
    """
    lunaLists = dbContext.getLunaListsByAccountLists(lists, accountId)
    dbContext.removeAccountLists(lists, accountId)

    yield lunaContext.removeListsFromLuna(lunaLists)


class ListHandler(StorageHandler):
    """
    Handler to operate with account lists. Before start you need to authorize and account must be active.
    """

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        """
        Resource to get all account lists

        .. http:get:: /storage/lists

            :optparam page: A number of page. Minimum 1, default 1.
            :optparam page_size: Number of lists of the same type on page.  Minimum 1, maximum 100, default 10.

            :reqheader Authorization: basic authorization

                **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            **Example response**:

            :statuscode 200: Object (person, descriptor) data is received successfully

            .. sourcecode:: http

               HTTP/1.1 200 Ok
               Vary: Accept
               Content-Type: application/json
               LUNA-Request-Id: 1516179740,c06887a2

            .. json:object:: info lists
                :showexample:

                :property person_lists: person lists
                :proptype person_lists: _list_(:json:object:`account_list`)
                :property descriptor_lists: descriptor lists
                :proptype descriptor_lists: _list_(:json:object:`account_list`)
                :property persons_list_count: number of person lists
                :proptype persons_list_count: int
                :property descriptors_list_count: number of descriptors lists
                :proptype descriptors_list_count: int

            Error message is returned in format :json:object:`server_error`.

            :statuscode 500: internal server error
        """
        page, pageSize = self.getPagination()

        response = yield self.luna3Client.lunaFaces.getLists(accountId=self.accountId, listType=1,
                                                             pageSize=pageSize, page=page,
                                                             raiseError=True)
        personsLists = [
            {"id": lunaList["list_id"], "list_data": lunaList["user_data"], "count": lunaList["person_count"]} for
            lunaList in response.json["lists"]]
        personsListCount = response.json["count"]
        payload = {"person_lists": personsLists}

        response = yield self.luna3Client.lunaFaces.getLists(accountId=self.accountId, listType=0,
                                                             pageSize=pageSize, page=page,
                                                             raiseError=True)

        descriptorsLists = [
            {"id": lunaList["list_id"], "list_data": lunaList["user_data"], "count": lunaList["face_count"]} for
            lunaList in response.json["lists"]]
        descriptorsListCount = response.json["count"]

        payload["descriptor_lists"] = descriptorsLists

        self.success(200, outputJson={"lists": payload, "persons_list_count": personsListCount,
                                      "descriptors_list_count": descriptorsListCount})

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def post(self):
        """
        Request for creation of new list for the account

        .. http:post:: /storage/lists?type=descriptors

            :optparam type: List type ("persons" or "descriptors", "persons" by default)

            :reqheader Authorization: basic authorization

                **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            .. sourcecode:: http

                POST /storage/lists HTTP/1.1
                Accept: application/json

            You can attach list data in format :json:object:`list_data`.

            **Example response**:

            :statuscode 201: List created successfully

            .. sourcecode:: http

               HTTP/1.1 201 Created
               Vary: Accept
               Content-Type: application/json
               LUNA-Request-Id: 1516179740,c06887a2

            .. json:object:: list_id
               :showexample:

               :property list_id: new list id
               :proptype list_id: uuid4

            Error message is returned in format :json:object:`server_error`.

            :statuscode 400: wrong format for 'type'
            :statuscode 400: field *list_data* is too large
            :statuscode 400: field *list_data* has wrong type, *string* type is required
            :statuscode 500: internal server error
        """
        listType = self.get_query_argument("type", None)
        #: TODO: make test type
        if listType is None or listType == "persons":
            typeList = 1
        else:
            if listType == "descriptors":
                typeList = 0
            else:
                error = Error.formatError(Error.BadQueryParams, 'type')
                return self.error(400, error)

        info = self.getInfoFromRequest("list_data")

        if type(info) != str:
            error = Error.formatError(Error.BadTypeOfFieldInJSON, 'list_data', 'string')
            return self.error(400, error)
        if len(info) > 128:
            return self.error(400, Error.BigUserData)
        response = yield self.luna3Client.lunaFaces.createList(self.accountId, info, typeList, raiseError=True)
        self.success(201, outputJson= response.json)

    @tornado.web.asynchronous
    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def delete(self):
        """
        Request for account lists deletion

        .. http:delete:: /storage/lists

            **Example request**:

            :reqheader Authorization: basic authorization

                **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            .. sourcecode:: http

                POST /accounts HTTP/1.1
                Accept: application/json
                LUNA-Request-Id: 1516179740,c06887a2

            .. json:object:: json for lists deletion
                :showexample:

                :property lists: list of tokens to delete
                :proptype lists: _list_(uuid4)

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 204 Ok
                Vary: Accept
                LUNA-Request-Id: 1516179740,c06887a2

            Message error is returned in format :json:object:`server_error`.

            :statuscode 400: no json in request
            :statuscode 400: no field *lists* in json
            :statuscode 400: field *lists* is not a list
            :statuscode 500: internal server error
        """

        strJson = self.request.body
        try:
            reqJson = tornado.escape.json_decode(strJson)
        except ValueError:
            self.logger.debug("failed decode json")
            return self.error(400, Error.RequestNotContainsJson)
        if reqJson is None:
            return self.error(400, Error.EmptyJson)
        if not ("lists" in reqJson):
            error = Error.formatError(Error.FieldNotInJSON, 'lists')
            return self.error(400, error)
        lists = reqJson["lists"]

        if type(lists) != list:
            error = Error.formatError(Error.BadTypeOfFieldInJSON, 'lists', 'list')
            return self.error(400, error)
        for accountList in lists:
            resCheckUUID = isUUID4(accountList)
            if not resCheckUUID:
                return self.error(400, Error.BadFormatUUID)

        yield self.luna3Client.lunaFaces.deleteLists(reqJson["lists"], self.accountId, raiseError=True)
        self.success(204)


class ListOfObjectHandler(StorageHandler):
    """
    Handler to work with account lists. Before start you need to authorize and account must be active.
    """

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def get(self, listId):
        """
        Request to get all objects in list.

        .. http:get:: /storage/lists/{listId}

            :param listId: list id

            :reqheader Authorization: basic authorization

                **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            **Example response**:

            :statuscode 200: objects list, number of objects and list_data are received successfully.

            .. sourcecode:: http

                HTTP/1.1 200 Ok
                Vary: Accept
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2

            Json example for persons list:

            .. json:object:: list_persons_json
                :showexample:

                :property persons: persons list
                :proptype persons: _list_(:json:object:`person`)
                :property count: number of objects in list
                :proptype count: int
                :property list_data: list data
                :proptype list_data: city

            Json example for descriptors list:

            .. json:object:: list_descriptors_json
                :showexample:

                :property persons: persons list
                :proptype persons: _list_(:json:object:`descriptor`)
                :property count: number of objects in list
                :proptype count: int
                :property list_data: list data
                :proptype list_data: city

            Message error is returned in format :json:object:`server_error`.

            :statuscode 404: list not found
            :statuscode 400: field *page* or *page_size* has wrong type
            :statuscode 500: internal server error

        """
        page, pageSize = self.getPagination()

        response = yield self.luna3Client.lunaFaces.getList(listId, self.accountId, raiseError=True,
                                                            pageSize=pageSize, page=page)
        lunaList = response.json

        if lunaList["type"]:
            self.success(200, outputJson={
                "persons": [{"id": person["person_id"], "create_time": functions.convertDateTime(person["create_time"]),
                             "lists": person["lists"], "descriptors": person["faces"], "user_data": person["user_data"],
                             "external_id": person["external_id"]} for person in lunaList["persons"]],
                "count": lunaList["person_count"], "list_data": lunaList["user_data"]})
        else:
            self.success(200, outputJson={"descriptors": [
                {"id": face["attributes_id"], "last_update": functions.convertDateTime(face["create_time"]),
                 "person_id": face["person_id"],
                 "lists": face["lists"]} for face in lunaList["faces"]],
                "count": lunaList["face_count"], "list_data": lunaList["user_data"]})

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def delete(self, listId):
        """
        Request for list deletion.

        .. http:delete:: /storage/lists/{listId}

            :param listId: list id

            :reqheader Authorization: basic authorization

                **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            **Example response**:

            :statuscode 204: list was deleted successfully.

            .. sourcecode:: http

                HTTP/1.1 204 Ok
                Vary: Accept
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2

            Message error is returned in format :json:object:`server_error`.

            :statuscode 404: list not found
            :statuscode 500: internal server error

        """
        yield self.luna3Client.lunaFaces.deleteList(listId, self.accountId, raiseError=True)

        self.success(204)

    @StorageHandler.requestExceptionWrap
    @gen.coroutine
    def patch(self, listId):
        """
        A request to change the data about the list.

        .. http:patch:: /storage/lists/{listId}

            :param listId: list id

            :reqheader LUNA-Request-Id: request id

            :reqheader Authorization: basic authorization

                **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            .. sourcecode:: http

                POST /storage/lists/{id} HTTP/1.1
                Accept: application/json

            Data has to be attached in format :json:object:`list_data`.

            **Example response**:

            :statuscode 204: list was modified successfully.

            .. sourcecode:: http

                HTTP/1.1 204 Ok
                Vary: Accept
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2

            Message error is returned in format :json:object:`server_error`.

            :statuscode 400: field *list_data* is too large
            :statuscode 400: field *list_data* has wrong type, *string* type is required
            :statuscode 404: list not found
            :statuscode 500: internal server error

        """
        info = self.getInfoFromRequest("list_data", True)

        if type(info) != str:
            error = Error.formatError(Error.BadTypeOfFieldInJSON, 'list_data', 'string')
            return self.error(400, error)
        if len(info) > 128:
            return self.error(400, Error.BigUserData)

        yield self.luna3Client.lunaFaces.updateListUserData(listId, info, self.accountId, raiseError=True)
        self.success(204)
