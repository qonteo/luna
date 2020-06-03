"""
Module realize handlers for work with persons.
"""
from luna3.common.exceptions import LunaApiException
from typing import Generator

from app.handlers.base_handler import BaseHandlerWithAuth
from tornado import gen

from common.api_clients import FACES_CLIENT
from common.query_validators import uuid4Getter
from crutches_on_wheels.errors.errors import Error


class PersonsHandler(BaseHandlerWithAuth):
    """
    Handler for getting persons.
    """

    @BaseHandlerWithAuth.requestExceptionWrap
    @gen.coroutine
    def get(self) -> Generator[None, None, None]:
        """
        Get persons with pagination.

        .. http:get:: /persons

            :query page: page count, default 1
            :query page_size: page size, default 10
            :query account_id: account id


            :reqheader Authorization: basic authorization

            **Example response**:


                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

                .. json:object:: luna_person_short

                    :property person_id: person id
                    :proptype person_id: uuid4
                    :property create_time: time of face creating
                    :proptype create_time: iso8601
                    :property account_id: account id
                    :proptype account_id: uuid4



                .. json:object:: list of persons
                    :showexample:

                    :property lists: lists
                    :proptype lists: _list_(:json:object:`luna_person_short`)
                    :property person_count: person count
                    :proptype person_count: integer

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: success
            :statuscode 400: Bad query parameters
            :statuscode 500: internal server error
        """
        page, pageSize = self.getPagination()
        accountId = self.getQueryParam("account_id", uuid4Getter, default=None)

        response = yield FACES_CLIENT.getPersons(accountId=accountId, page=page, pageSize=pageSize, raiseError=True,
                                                 lunaRequestId=self.requestId)
        res = {"person_count": response.json["count"], "persons": [{"create_time": person["create_time"],
                                                                    "account_id": person["account_id"],
                                                                    "person_id": person["person_id"]} for person in
                                                                   response.json["persons"]]}
        return self.success(200, outputJson=res)


class PersonHandler(BaseHandlerWithAuth):

    @BaseHandlerWithAuth.requestExceptionWrap
    @gen.coroutine
    def get(self, personId: str) -> Generator[None, None, None]:
        """

        Request to get the person.

        :param personId: person id

        Resource is reached by address '/persons/{personId}'

        .. http:get:: /persons/{personId}

            :param personId: person id

            :reqheader LUNA-Request-Id: request id

            :query account_id: account id, this parameter determine, that action must be done with only with objects
                               of this account.

            .. sourcecode:: http

                GET /persons/{personId} HTTP/1.1

            **Example response**:


                .. sourcecode:: http

                    HTTP/1.1 200
                    Begin-Request-Time: 1526039272.9173293
                    End-Request-Time: 1526039272.9505265
                    LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                    Content-Type: application/json


            Output account will be represent in  :json:object:`luna_person`

            :statuscode 200: Ok
            :statuscode 404: person not found
            :statuscode 500: internal server error

        """
        try:
            response = yield FACES_CLIENT.getPerson(personId=personId, raiseError=True, lunaRequestId=self.requestId)
            return self.success(200, outputJson=response.json)
        except LunaApiException as e:
            if e.statusCode == 404:
                return self.error(404, error=Error.PersonNotFound)
            else:
                raise
