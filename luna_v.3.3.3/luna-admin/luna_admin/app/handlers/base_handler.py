import base64
from tornado import escape
from typing import Optional
from common.object_getters import ObjectGetters
from app.admin_db.db_context import DBContext as AdminDBContext
from app.api_db.db_function import DBContext as ApiDBContext
import ujson as json
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.handlers.base_handler_class import VLBaseHandler


class BaseHandler(VLBaseHandler):
    """
    Base class for handlers.
    """

    def initialize(self):
        """
        Initialize logger for request and  create request id and contexts to Postgres and LunaCore.
        Initialize admin db context.
        RequestId consists of two parts. first - timestamp of server time or utc, second - short uuid4.
        """
        super().initialize()
        self.dbAdminContext = AdminDBContext(self.logger)

    def verifyAuth(self, authStr: str) -> bool:
        """
        Verify input auth string
        Args:
            authStr: auth string

        Returns:
            True if success otherwise False
        """
        authBase64 = authStr[len("Basic "):]

        try:
            authData = base64.b64decode(authBase64).decode("utf-8")
        except ValueError:
            return False
        colonIndex = authData.index(":")
        login = authData[0:colonIndex]
        password = authData[colonIndex + 1:]
        authRes = self.dbAdminContext.authAdmin(login, password)
        return authRes

    def badAuth(self, errCode: int, msg: str) -> None:
        """
        Response to unsuccessful attempt to access resource, which requires authorization.

        Response contains header 'WWW-Authenticate' with description of authorization format.
        Response body contains json with error description.

        Args:
            errCode: error code
            msg: error message
        """
        self.set_header('Content-Type', 'application/json')
        self.set_header('WWW-Authenticate', 'Basic realm="login:password"')
        self.set_status(401)
        self.finish(json.dumps({'error_code': errCode,
                                'detail': msg}, ensure_ascii=False))

    def get_current_user(self) -> Optional[str]:
        """
        Get auth cookies.

        Returns:
            auth cookies or None
        """
        authHeader = self.get_secure_cookie("admin_auth")
        if authHeader is None:
            return None
        else:
            if not self.verifyAuth(authHeader.decode("utf-8")):
                return None
            return authHeader.decode("utf-8")


class BaseHandlerWithAuth(BaseHandler):
    """
    All handlers with authorization classes must be inherited from this class.
    """

    def initialize(self):
        """
        Initialize api db context
        """
        super().initialize()
        self.dbApiContext = ApiDBContext(self.logger)
        self.objectGetters = ObjectGetters(self.dbApiContext, self.requestId)

    def prepare(self) -> None:
        """
        Check auth before processing request.
        """
        self.checkAuth()

    def checkAuth(self) -> None:
        """
        Check  basic auth or cookies.
        """
        authHeader = self.request.headers.get('Authorization', None)
        if authHeader is None and not self.current_user:
            if not self.current_user:
                return self.badAuth(Error.BadHeaderAuth.errorCode, Error.BadHeaderAuth.description)
        if authHeader is not None:
            try:
                if not self.verifyAuth(authHeader):
                    self.badAuth(Error.AccountNotFound.errorCode, Error.AccountNotFound.description)
            except Exception:
                return self.badAuth(Error.AccountNotFound.errorCode, Error.AccountNotFound.description)


class LoginHandler(BaseHandler):

    """
    Login handler
    """

    def post(self) -> None:
        """
        Create auth cookies

        .. http:post:: /login

            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 201 Created
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

            Message error is returned in format :json:object:`server_error`.

            :statuscode 201: cookies was set successfully.
            :statuscode 500: internal server error

        """
        authHeader = self.request.headers.get('Authorization', None)
        if authHeader is None:
            self.badAuth(Error.BadHeaderAuth.errorCode, Error.BadHeaderAuth.description)
        else:
            try:
                auth = self.verifyAuth(authHeader)
            except Exception:
                return self.badAuth(Error.AccountNotFound.errorCode,
                                    Error.AccountNotFound.description)

            if not auth:
                self.badAuth(Error.AccountNotFound.errorCode,
                             Error.AccountNotFound.description)
            else:
                self.set_secure_cookie("admin_auth", authHeader)
                self.set_status(201)
                self.finish()

    def delete(self) -> None:
        """
        Clear auth cookie

        .. http:delete:: /login

            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 204 Deleted
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

            Message error is returned in format :json:object:`server_error`.

            :statuscode 204: cookies was set successfully.
            :statuscode 500: internal server error

        """
        self.clear_cookie("admin_auth")
        self.set_status(204)
        self.finish()

    def get(self) -> None:
        """
        Check auth cookie

        .. http:get:: /login

            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: cookies  is correctly
            :statuscode 401: unauthorized
            :statuscode 500: internal server error

        """
        if not self.current_user:
            return self.badAuth(401, Error.BadHeaderAuth.description)
        self.write("Ok")
        self.finish()

    @BaseHandlerWithAuth.requestExceptionWrap
    def patch(self) -> None:
        """
        Change login

        .. http:patch:: /login

            :reqheader Authorization: basic authorization

            **Example request**:

                .. sourcecode:: http

                    PATCH /login HTTP/1.1
                    Accept: application/json

                .. json:object:: server_error
                    :showexample:

                    :property string password: new password


            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 204 success change password
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: cookies  is correctly
            :statuscode 400: bad json
            :statuscode 401: unauthorized
            :statuscode 500: internal server error

        """
        authHeader = self.request.headers.get('Authorization', None)
        if authHeader is None:
            return self.badAuth(Error.BadHeaderAuth.errorCode,
                                Error.BadHeaderAuth.description)
        try:
            auth = self.verifyAuth(authHeader)
            if not auth:
                return self.badAuth(Error.AccountNotFound.errorCode,
                                    Error.AccountNotFound.description)
        except Exception:
            return self.badAuth(Error.AccountNotFound.errorCode,
                                Error.AccountNotFound.description)
        try:
            reqJson = escape.json_decode(self.request.body)

        except Exception:
            raise VLException(Error.RequestNotContainsJson, 400)
        if "password" not in reqJson:
            error = Error.generateError(Error.FieldNotInJSON,
                                        Error.FieldNotInJSON.description.format("password"))
            raise VLException(error, 400)
        if type(reqJson["password"]) != str:
            error = Error.generateError(Error.BadTypeOfFieldInJSON,
                                        Error.BadTypeOfFieldInJSON.description.format("password", "str"))
            raise VLException(error, 400)
        password = reqJson["password"]
        self.dbAdminContext.changeAdminPassword(password)
        self.success(204)
