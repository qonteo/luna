# -*- coding: utf-8 -*-

import time
import ujson as json

from tornado import gen, web, httpclient
from tornado.httpclient import HTTPRequest

from app.admin_stats import AdminStats
from app.common import ACCOUNT_STATISTICS_PLUGINS
from app.functions import generateStatsTornadoRequestError
from app.rest_handlers.account_handler import AccountHandlerBase
from app.rest_handlers.authorization import tokenAuth, basicAuth, accountIsActive
from app.tornado_request_function import queryExtractImgParam
from configs.config import ADMIN_STATISTICS_SERVER_ORIGIN, ADMIN_STATISTICS_DB, ACCOUNTS_STATISTICS_SERVER, \
    SEND_ACCOUNT_STATS, SEND_ADMIN_STATS, SERVER_IP
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.utils.timer import timer


class StorageHandlerBase(AccountHandlerBase):
    """
    Bases class for authorization by token an login/password.
    """

    def prepare(self):
        if self.request.method == "OPTIONS":
            return
        try:

            if self.get_cookie("Authorization"):
                cookie = self.get_cookie("Authorization")
                authRes = cookie[:5] + " " + cookie[5:]
                authHeaderToken = None
                authHeaderBasic = None

                if cookie[:5] == "token":
                    authHeaderToken = authRes
                elif cookie[:5] == "Basic":
                    authHeaderBasic = authRes

            else:
                authHeaderToken = self.request.headers.get('X-Auth-Token', None)
                authHeaderBasic = self.request.headers.get('Authorization', None)

            if authHeaderToken:
                self.auth = authHeaderToken
                self.accountId = tokenAuth(authHeaderToken, self.dbContext)

            elif authHeaderBasic:
                self.auth = "basic"
                self.accountId = basicAuth(authHeaderBasic, self.dbContext)
            else:
                error = Error.formatError(Error.BadHeaderAuth, 'X-Auth-Token or Authorization')
                return self.error(401, error)
        except VLException as e:
            if e.error == Error.BadHeaderAuth:
                return self.badAuth(e.error.errorCode,
                                    e.error.detail.format('X-Auth-Token or Authorization'),
                                    'Basic realm="login:password" or token')
            elif e.error == Error.AccountNotFound:
                return self.badAuth(e.error.errorCode, e.error.detail,
                                    'Basic realm="login:password" or token')
            elif e.error == Error.BadFormatUUID:
                return self.badAuth(e.error.errorCode, e.error.detail,
                                    'Basic realm="login:password" or token')
            else:
                return self.error(500, e.error)

        except Exception:
            self.logger.exception()
            self.error(500, Error.AuthFailedError)


class LoginHandler(StorageHandlerBase):
    """
    Handler for installation of cookies and for account id receipt.
    """

    def prepare(self):
        super().prepare()

    @web.asynchronous
    @StorageHandlerBase.requestExceptionWrap
    def get(self):
        """
        Get account id.

        .. http:get:: /login

            :reqheader Authorization: basic authorization

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200 Ok
                Vary: Accept
                Content-Type: text/html

        """
        self.write(self.accountId)
        self.set_header('Content-Type', 'text/html')
        self.set_status(200)
        self.finish()

    @web.asynchronous
    @StorageHandlerBase.requestExceptionWrap
    def post(self):
        """
        Install cookies for authorization.

        .. http:post:: /login

            :reqheader Authorization: basic authorization

            **Example response**:

            :statuscode 200: cookie is successfully installed

            .. sourcecode:: http

                HTTP/1.1 200 Ok
                Vary: Accept
                Content-Type: application/json

            :statuscode 204: cookies are already installed

            .. sourcecode:: http

                HTTP/1.1 204 Ok
                Vary: Accept
                Content-Type: application/json

        """
        #: TODO cookies for token
        if not self.get_cookie("Authorization"):
            t = self.request.headers.get('Authorization', None).split()
            self.set_cookie("Authorization", t[0] + t[1])
            self.write("Created")
            self.set_header('Content-Type', 'text/html')
            self.set_status(201)
            self.finish()
        else:
            self.success(204)

    @web.asynchronous
    @StorageHandlerBase.requestExceptionWrap
    def delete(self):
        """
        Delete cookies

        .. http:delete:: /login

        :reqheader Authorization: basic authorization

        **Example response**:

        :statuscode 204: cookies are deleted successfully

        .. sourcecode:: http

            HTTP/1.1 204 Ok
            Vary: Accept
            Content-Type: application/json

        """
        self.clear_cookie("Authorization")
        self.success(204)


class StorageHandler(StorageHandlerBase):
    """
    Authentication for accessing account data (such as lists, persons, descriptors) and matching.
    This method is called before any client request associated with account data.
    This method does installation in case of successful authentication *self.accountId*.

    For authentication you can use basic authorization or authentication by token.

    Basic authorization. In header you need to put field *Authorization*
    with value *'Basic login:password'*. String *'login:password'* contains login/password for access to account, whole
    string must be converted to base64.

    Authentication by token. In header you need to put field  *X-Auth-Token*
    with value of token from this account.

    .. http:any:: /

        :reqheader Authorization: basic authorization

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 401 Unauthorized
            Vary: Reject
            Content-Type: application/json
            'WWW-Authenticate': 'Basic realm="login:password" or token'

        Error message is returned in format :json:object:`server_error`.

        :statuscode 401: no authorization header
        :statuscode 401: authorization header is not basic authorization
        :statuscode 401: account not found for these login/password
        :statuscode 403: account is currently inactive
        :statuscode 500: internal server error
    """

    def prepare(self):
        if self.request.method == "OPTIONS":
            return
        try:

            super().prepare()

            if hasattr(self, "accountId"):
                accActive = accountIsActive(self.accountId, self.dbContext)
                if not accActive:
                    return self.error(403, Error.AccountIsNotActive)

        except Exception:
            self.logger.exception()
            self.error(500, Error.AuthFailedError)

    def fillQueryParams(self):
        """
        Fill the parameter structure to extract from query.
         
        :return: structure with parameters
        """
        qParams = queryExtractImgParam()
        for param in qParams.getStore():
            queryParam = self.get_query_argument(param, None)
            if queryParam is not None:
                try:
                    qParams[param] = type(qParams[param])(queryParam)
                except ValueError:
                    self.logger.debug("failed convert param {} to int".format(param))
        return qParams

    def setAdditionalDataToAccountStatistic(self, accountStats):
        """
        For childes of  *StorageHandler* method of set additional account stats

        :param accountStats: common stats
        :return: new stats
        """
        return accountStats

    def getAuthForStats(self):
        """
        Get authorization for account stats.

        :return: if success "basic" or :json:object:`auth_token`, if failed None
        """
        if self.auth == "basic":
            return self.auth

        tokenRes = self.dbContext.getTokenById(self.auth, self.accountId)
        return {"token_id": self.auth, "token_data": tokenRes}

    def generateAccountStats(self):
        """
        Generate common json-dict to send client statistics.

        :return: in case of exception None is returned, in other cases:

            .. json:object:: client_stats
                :showexample:
            
                :property result: json with request results.
                :proptype result: :json:object:`identify_result`
                :property account_id: id account
                :proptype account_id: uuid4
                :property event_type: type of event ("match", "extract")
                :proptype event_type: "match"
                :property authorization: authorization, "basic" or :json:object:`auth_token`
                :proptype authorization: :json:object:`auth_token`
                :property source: request resource ("match", "descriptors")
                :proptype source: 'match'
        """
        try:
            payload = {"result": self.statistiData.responseJson}
            payload["account_id"] = self.accountId
            payload["timestamp"] = time.time()
            payload["source"] = self.getResource()
            if payload["source"] in ["match", "search", "identify", "verify"]:
                payload["event_type"] = "match"
            elif payload["source"] in ["descriptors"]:
                payload["event_type"] = "extract"
            else:
                payload["event_type"] = "unknown"
                self.logger.error("unknown event type")
            payload["authorization"] = self.getAuthForStats()
            payload = self.setAdditionalDataToAccountStatistic(payload)
            return payload
        except Exception:
            self.logger.exception()
            return None

    def generateAdminStatisticsRequestBody(self):
        """
        Generate body request to send admin statistics.


        :return: 1) in case of success following string is generated *"extract_success,resource=/descriptors,\
         server=127.0.0.1,account_id=16fd2706-8baf-433b-82eb-8c7fada847da,count_faces=1 value_time=0.33"*
                 #) in case of failure following string is generated *"errors,resource=/descriptors,server=127.0.0.1,\
         account_id=16fd2706-8baf-433b-82eb-8c7fada847da,error=2 value=2"*

        """
        if self.statistiData.isSuccess:
            resource = self.getResource()
            if resource == "descriptors":
                adminStats = AdminStats("extract_success")
            elif resource in ["match", "search", "identify", "verify"]:
                adminStats = AdminStats("matching_success")
            else:
                adminStats = AdminStats("unknown")

            tags = {"resource": self.getResource(),
                    "server": SERVER_IP,
                    "account_id": self.accountId}
            values = {"value_time": str(self.statistiData.requestTime)}
            adminStats.update(tags, values)
            adminStats = self.setAdditionalDataToAdminStatistic(adminStats)
            return adminStats.getStrToInfluxRequest()
        else:
            return self.generateErrorStatisticsRequestBody()

    def setAdditionalDataToAdminStatistic(self, adminStats):
        """
        For childes of  *StorageHandler* method of set additional admin stats

        :param adminStats: common stats
        :return: new stats
        """
        return adminStats

    @gen.coroutine
    def setListDataToAccountStats(self, stats: dict) -> None:
        """
        Add list data to matching statistics.

        :param stats: account statistics

        """
        if stats["source"] in ("search", "identify", "match"):
            if "list_id" in stats["candidate"]:
                lunsList = yield self.luna3Client.lunaFaces.getList(stats["candidate"]["list_id"], pageSize=0,
                                                                    raiseError=True)
                stats["candidate"]['list_data'] = lunsList.json["user_data"]
                stats["candidate"]['list_type'] = lunsList.json["type"]


    @timer
    @gen.coroutine
    def sendStats(self):
        """
        Function to send statistics. Called, when account has already received answer in method *on_finish*.
        """
        accountStats = None
        if SEND_ADMIN_STATS or len(ACCOUNT_STATISTICS_PLUGINS) > 0:
            accountStats = self.generateAccountStats()
            if accountStats is not None:
                yield self.setListDataToAccountStats(accountStats)
        try:
            http_client = httpclient.AsyncHTTPClient()
            statisticRequests = []
            if SEND_ADMIN_STATS:
                influxRequest = self.generateAdminStatisticsRequestBody()
                request = HTTPRequest(ADMIN_STATISTICS_SERVER_ORIGIN + "/write?db=" + ADMIN_STATISTICS_DB,
                                      body=influxRequest,
                                      method="POST",
                                      headers={"Content-Type": "application/json"})
                statisticRequests = [(http_client.fetch(request, raise_error=False), "admin")]
            if SEND_ACCOUNT_STATS:
                if accountStats is not None:
                    requestAccountStatistics = HTTPRequest(ACCOUNTS_STATISTICS_SERVER + "/",
                                                           body=json.dumps(accountStats, ensure_ascii=False),
                                                           method="POST",
                                                           headers={"Content-Type": "application/json",
                                                                    "LUNA-Request-Id": self.requestId})

                    statisticRequests.append(
                        (http_client.fetch(requestAccountStatistics, raise_error=False), "account"))

            for request in statisticRequests:
                reply = yield request[0]
                if not (200 <= reply.code < 300):
                    self.logger.warning("Failed send {} statistics".format(request[1]))
                    if reply.code == 599:
                        generateStatsTornadoRequestError(reply, "{} stats server".format(request[1]), self.logger)
                    else:
                        try:
                            self.logger.warning(
                                "Send statistics {} error, status code: {}".format(request[1], str(reply.code)))
                            self.logger.warning("Response body: {}".format(reply.body.decode("utf-8")))
                        except Exception as e:
                            self.logger.error(str(e))
            try:
                for plugin in ACCOUNT_STATISTICS_PLUGINS:
                    if accountStats is not None:
                        yield plugin(accountStats, self.requestId, self.logger)
            except Exception as e:
                self.logger.exception("exception in account statistics plugin")
        except Exception as e:
            self.logger.exception()
