import base64

from tornado import gen

from app.handlers.base_handler import BaseHandlerWithAuth
from luna3.admin.admin import AdminApi

from configs.comand_line_args_parser import getOptionsParser
from configs.config import ADMIN_REQUEST_TIMEOUT, ADMIN_CONNECT_TIMEOUT

OPTIONS = getOptionsParser()


class TemplateBaseHandler(BaseHandlerWithAuth):

    @BaseHandlerWithAuth.requestExceptionWrap
    @gen.coroutine
    def prepare(self):
        if not self.current_user:
            return self.redirect("/login")

        super().prepare()
        if self._finished:
            return

        authHeader = self.get_secure_cookie("admin_auth")
        if not authHeader:
            authHeader = self.request.headers.get('Authorization', None)
        authBase64 = authHeader[len("Basic "):]

        authData = base64.b64decode(authBase64).decode("utf-8")

        colonIndex = authData.index(":")
        login = authData[0:colonIndex]
        password = authData[colonIndex + 1:]

        self.adminClient = AdminApi(login, password, "http://127.0.0.1:{}".format(OPTIONS.back_port), asyncRequest=True,
                                    api=2, lunaRequestId=self.requestId, connectTimeout=ADMIN_CONNECT_TIMEOUT,
                                    requestTimeout=ADMIN_REQUEST_TIMEOUT)
