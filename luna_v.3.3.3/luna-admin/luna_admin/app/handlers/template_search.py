from tornado import gen

from app.handlers.temlate_base_handler import TemplateBaseHandler
from crutches_on_wheels.errors.errors import Error


class TemplateSeacrhHandler(TemplateBaseHandler):

    @TemplateBaseHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        accountEmail = self.getQueryParam('account_email')
        if accountEmail is None:
            error = Error.generateError(Error.QueryParameterNotFound,
                                        Error.QueryParameterNotFound.getDescription().format("account_email"))
            return self.error(400, error=error)

        searchRes = (yield self.adminClient.search(accountEmail, raiseError=True)).json
        if not searchRes["data"]:
            error = Error.generateError(Error.AccountNotFound,
                                        "Account with this email not found")
            return self.error(400, error=error)
        self.success(200, outputJson=searchRes["data"]["info"]["account_id"])
