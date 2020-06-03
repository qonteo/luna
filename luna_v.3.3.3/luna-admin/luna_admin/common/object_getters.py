"""
Module provides function for getting objects by id.
"""
from typing import Generator, Union, Optional
from app.api_db.db_function import DBContext as ApiDBContext
from tornado import gen
from common.api_clients import FACES_CLIENT
from app.utils.functions import getRequestId


class ObjectGetters:
    """
    Class with object getters functions
    """

    def __init__(self, dbApiContext: Optional[ApiDBContext] = None, requestId: Optional[str] = None) -> None:
        """
        Initialization
        Args:
            dbApiContext: api db context
            requestId: luna request id
        """
        self.requestId = getRequestId(requestId)
        self.dbApiContext = dbApiContext

    @gen.coroutine
    def getAccountStats(self, accountId: str) -> Generator[None, None, dict]:
        """
        Get account stats (count of person, descriptor, token, list).
        Args:
            accountId: account id

        Returns:
            dict with corresponding values
        """
        countAccountLists = \
        (yield FACES_CLIENT.getLists(accountId=accountId, raiseError=True, lunaRequestId=self.requestId)).json["count"]
        countDescriptors = \
        (yield FACES_CLIENT.getFaces(accountId=accountId, raiseError=True, lunaRequestId=self.requestId)).json["count"]
        countPerson = \
        (yield FACES_CLIENT.getPersons(accountId=accountId, raiseError=True, lunaRequestId=self.requestId)).json[
            "count"]
        countToken = self.dbApiContext.getCountTokens(accountId)
        return {"person_count": countPerson, "descriptor_count": countDescriptors, "token_count": countToken,
                "list_count": countAccountLists}

    def getAccount(self, accountId: str) -> Union[dict, None]:
        """
        Get account data (email, organization name, status)

        Args:
            accountId: account id

        Returns:
            account data if the account exists otherwise None
        """
        res = self.dbApiContext.getAccount(accountId)
        if res is None:
            return None
        account = {"organization_name": res[0], "email": res[1],
                   "account_id": accountId, "status": int(res[2])}

        return account

    @gen.coroutine
    def getAccountInfo(self, accountId) -> Generator[None, None, Union[dict, None]]:
        """
        Get account with data and stats.

        Args:
            accountId: account id

        Returns:
            dict with keys "info" and "stats" if the corresponding account exists otherwise None

        """
        accountInfo = self.getAccount(accountId)
        if accountInfo is None:
            return None
        stats = yield self.getAccountStats(accountId)

        return {"info": accountInfo, "stats": stats}

    @gen.coroutine
    def getListInfo(self, listId: str) -> Generator[None, None, dict]:
        """
        Get list info by id (list id, account id, last update time, count object in list, user data, type).

        Args:
            listId: list id

        Returns:
            dict with corresponding keys  the list existst otherwise None
        Raises:
            LunaApiException: if list not found or request failed will raise exception
        """
        response = yield FACES_CLIENT.getList(listId=listId, raiseError=True, lunaRequestId=self.requestId)
        lunaList = response.json
        return {"list_id": lunaList["list_id"], "account_id": lunaList["account_id"],
                "last_update_time": lunaList["last_update_time"],
                "count_object_in_list": lunaList["person_count"] if lunaList["type"] else lunaList["face_count"],
                "user_data": lunaList["user_data"], "type": lunaList["type"]}

    @gen.coroutine
    def getPersonInfo(self, personId: str) -> Generator[None, None, dict]:
        """
        Get person info by id (person id, lists, create time, faces, user data).

        Args:
            personId: person id

        Returns:
            dict with corresponding keys  if the person exists otherwise None

        Raises:
            LunaApiException: if person not found or request failed will raise exception
        """
        response = yield FACES_CLIENT.getPerson(personId=personId, raiseError=True, lunaRequestId=self.requestId)
        return response.json

    @gen.coroutine
    def getFaceInfo(self, descriptorId: str) -> Generator[None, None, dict]:
        """
        Get face info by id (person id, lists, create time, last update time).

        Args:
            descriptorId: person id

        Returns:
            dict with corresponding keys if face exists otherwise None

        Raises:
            LunaApiException: if face not found or request failed will raise exception
        """
        response = yield FACES_CLIENT.getFace(faceId=descriptorId, raiseError=True, lunaRequestId=self.requestId)
        return {"create_time": response.json["create_time"], "account_id": response.json["account_id"],
                "face_id": response.json["face_id"], "person_id": response.json["person_id"]}
