from tornado import gen

import ujson as json

from app.handlers.temlate_base_handler import TemplateBaseHandler
from common.pagging import getPages


class TemplateAccountHandler(TemplateBaseHandler):

    @TemplateBaseHandler.requestExceptionWrap
    @gen.coroutine
    def get(self, accountId):
        account = (yield self.adminClient.getAccount(accountId, raiseError=True)).json
        account["info"]["id"] = account["info"]["account_id"]

        return self.render("templates/account.html", **account["info"], **account["stats"])


class TemplateAccountListsHandler(TemplateBaseHandler):

    @TemplateBaseHandler.requestExceptionWrap
    @gen.coroutine
    def get(self, accountId):
        page, pageSize = self.getPagination()
        lists = (yield self.adminClient.getLists(None, accountId, page, pageSize, raiseError=True)).json

        paging = getPages(page, pageSize, lists["list_count"])
        return self.render("templates/accounts_lists_tabel.html", lists=lists["lists"], account_id=accountId,
                           **paging)


class TemplateAccountTokensHandler(TemplateBaseHandler):

    @TemplateBaseHandler.requestExceptionWrap
    @gen.coroutine
    def get(self, accountId):
        page, pageSize = self.getPagination()
        tokens = (yield self.adminClient.getAccountToken(accountId, page, pageSize, raiseError=True)).json

        paging = getPages(page, pageSize, tokens["token_count"])
        return self.render("templates/accounts_tokens_tabel.html", tokens=tokens["tokens"], account_id=accountId,
                           **paging)
