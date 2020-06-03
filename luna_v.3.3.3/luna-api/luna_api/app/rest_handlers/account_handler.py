import ujson as json


from tornado import escape, gen
from tornado import web
from app.rest_handlers.authorization import basicAuth, accountIsActive
from crutches_on_wheels.utils.timer import timer
from configs.config import SERVER_IP
from crutches_on_wheels.errors.errors import Error
from app.rest_handlers.base_handler_class import BaseRequestHandler
from crutches_on_wheels.errors.exception import VLException


class AccountHandlerBase(BaseRequestHandler):
    """
    Parent class, all account access handlers are inherited from this class.
    Class contains all statistics data (StatisticsData), which is collected after request is terminated 
    (except start time of the request).
    """

    def prepare(self):
        """
        Account authentication. This method is called before any client request, which refers to account data access, is
        executed. This method executes installation, in case of success system returns *self.accountId*.

        For authenication basic authorization is used. Field *Authorization* with value *'Basic login:password'* 
        has to be put in header. String *'login:password'* contains login/password for access to account,
        string has to be converted to base64.

        .. http:any:: /

            :reqheader Authorization: basic authorization

            :reqheader LUNA-Request-Id: some id

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 401 Unauthorized
                Vary: Reject
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2
                'WWW-Authenticate': 'Basic realm="login:password"'


            Error message is returned in format :json:object:`server_error`.
            
            :statuscode 401: no header for authorization
            :statuscode 401: header for authorization is not basic authorization
            :statuscode 401: account not found
            :statuscode 500: internal server error
        """
        if self.request.method == "OPTIONS":
            return
        try:
            if self.get_cookie("Authorization"):
                cookie = self.get_cookie("Authorization")
                authRes = basicAuth(cookie[:5] + " " + cookie[5:], self.dbContext)
            else:
                authHeader = self.request.headers.get('Authorization', None)
                authRes = basicAuth(authHeader, self.dbContext)

            self.accountId = authRes

        except VLException as e:
            if e.error == Error.BadHeaderAuth:
                self.badAuth(e.error.errorCode,
                             e.error.detail.format("Authorization"),
                             'Basic realm="login:password"')
            elif e.error == Error.AccountNotFound:
                self.badAuth(e.error.errorCode, e.error.detail, 'Basic realm="login:password"')
            else:
                self.error(e.statusCode, e.error)
        except Exception:
            self.logger.exception()
            self.error(500, Error.AuthFailedError)

    def badAuth(self, errCode, msg, authHeader):
        """
        Response to unsuccessful attempt to access resource, which requires authorization.

        Response contains header 'WWW-Authenticate' with description of authorization format.
        Response body contains json with error description.
        """
        self.set_header('Content-Type', 'application/json')
        self.set_header('WWW-Authenticate', authHeader)
        self.set_status(401)
        self.finish(json.dumps({'error_code': errCode,
                                'detail': msg}, ensure_ascii=False))

    def generateErrorStatisticsRequestBody(self):
        """
        Create request in error series in influx database. 
        
        :return: request string.
        """
        influxRequest = "errors"
        influxRequest += ",resource=" + self.getResource()
        influxRequest += ",server=" + SERVER_IP
        if hasattr(self, "accountId"):
            influxRequest += ",account_id=" + self.accountId
        influxRequest += ",error=" + str(self.getErrorCode())

        influxRequest += " error_code=" + str(self.getErrorCode())
        return influxRequest

    def getResource(self):
        """
        Get resource of request (last part)
        
        :return: string, for example "/persons"
        """
        return self.request.uri.split("/")[-1:][0].split('?')[0]

    def getErrorCode(self):
        """
        Get error code from dict by key "error_code".
        """
        return self.statistiData.responseJson["error_code"]

    def getInfoFromRequest(self, key, isRequired=False, default="") -> str:
        """
        Get data from json by key.

        If param does not found and it is required, return None
        :param key: str-key of request
        :param isRequired: required param or not.
        :param default: default value
        :return: if no key was found, empty string is returned
        """
        strJson = self.request.body
        try:
            reqJson = escape.json_decode(strJson)
        except Exception as e:
            self.logger.debug(str(e))
            if isRequired:
                raise VLException(Error.RequestNotContainsJson, 400, isCriticalError=False)
            reqJson = None

        info = default
        if reqJson is not None:
            try:
                if key in reqJson:
                    info = reqJson[key]
                elif isRequired:
                    error = Error.formatError(Error.FieldNotInJSON, key)
                    raise VLException(error, 400, isCriticalError=False)
            except VLException:
                raise
            except Exception:
                raise VLException(Error.RequestNotContainsJson, 400, isCriticalError=False)

        return info


class AccountHandlerActive(AccountHandlerBase):
    """
    Class to access account data requiring authentication and verification that the account is active.
    """

    @AccountHandlerBase.requestExceptionWrap
    def prepare(self):
        """
        Prepare for execution of main request, perform authentication and check, whether account is active or not.

        .. http:any:: /

            :reqheader Authorization: basic authorization

            :reqheader LUNA-Request-Id: some id

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 401 Unauthorized
                Vary: Reject
                Content-Type: application/json
                'WWW-Authenticate': 'Basic realm="login:password"'
                LUNA-Request-Id: 1516179740,c06887a2

            .. sourcecode:: http

                HTTP/1.1 403 Forbiden
                Vary: Reject
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2
                
            Error message is returned in format :json:object:`server_error`.
            
            :statuscode 403: account is currently blocked
        """

        super(AccountHandlerActive, self).prepare()

        if hasattr(self, "accountId"):
            if self.accountId is not None:
                accState = accountIsActive(self.accountId, self.dbContext)
                if not accState:
                    self.error(403, Error.AccountIsNotActive)


class AccountInfoHandler(AccountHandlerBase):
    """
    Handler to get account information, only authorization is required.
    """

    @web.asynchronous
    @AccountHandlerBase.requestExceptionWrap
    def get(self):
        """
        .. http:get:: /account

            :reqheader Authorization: basic authorization

            :reqheader LUNA-Request-Id: some id

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200 Ok
                Vary: Accept
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2

            .. json:object:: account_info
                :showexample:

                :proptype email: email
                :proptype organization_name: user_name
                :property email: account e-mail
                :property organization_name: organization name
                :property suspended: if account is currently blocked, system returns *True*
                :proptype suspended: boolean
                
            Error message is returned in format :json:object:`server_error`.
            
            :statuscode 500: internal server error
        """
        account = self.dbContext.getAccountByAccountId(self.accountId)
        self.success(200, outputJson={"email": account.email, "organization_name": account.organization_name,
                                      "suspended": (not account.active)})


class AccountStatsHandler(AccountHandlerBase):
    """
    Handler to receive account statistics.
    """

    @timer
    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        """
        Get account statistics
        
        .. http:get:: /account/statistics

            :reqheader Authorization: basic authorization

            :reqheader LUNA-Request-Id: some id

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200 Ok
                Vary: Accept
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2
            
            :statuscode 200: statistics successfully received
            
            .. json:object:: account_stats
                :showexample:

                :property count_persons: number of persons, linked to account
                :proptype count_persons: integer
                :property count_descriptors: number of descriptors, linked to account
                :proptype count_descriptors: integer
                :property attached_descriptors: number of descriptors, linked to account persons
                :proptype attached_descriptors: integer

            Error message is returned in format :json:object:`server_error`.
            :statuscode 500: internal server error      
        """

        countPersResponse = yield self.luna3Client.lunaFaces.getPersons(accountId=self.accountId, raiseError=True)
        countPers = countPersResponse.json["count"]
        countDescriptorsResponse = yield self.luna3Client.lunaFaces.getFaces(accountId=self.accountId, raiseError=True)
        countDescriptors = countDescriptorsResponse.json["count"]
        self.success(200, outputJson={"count_persons": countPers,
                                      "count_descriptors": countDescriptors,
                                      "attached_descriptors": None})
