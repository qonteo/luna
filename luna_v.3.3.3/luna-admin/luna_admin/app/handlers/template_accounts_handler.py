from tornado import gen
from app.handlers.temlate_base_handler import TemplateBaseHandler
from common.api_clients import FACES_CLIENT
from common.pagging import getPages


class TemplateAccountsHandler(TemplateBaseHandler):

    @TemplateBaseHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        page, pageSize = self.getPagination()
        accounts = (yield self.adminClient.getAccounts(page, pageSize, self.requestId, raiseError=True)).json
        getStatus = lambda account: "active" if account["status"] else "suspended"

        paging = getPages(page, pageSize, accounts["account_count"])
        accounts = [( account["organization_name"], account["email"], getStatus(account),account["account_id"]) for
                    account in accounts["accounts"]]
        countsDict = yield self.getCountStats()
        return self.render("templates/accounts.html", **paging, items=accounts, **countsDict)

    @gen.coroutine
    def getCountStats(self):
        countAccountLists = (yield self.adminClient.getLists(raiseError=True)).json["list_count"]
        countDescriptors = (yield FACES_CLIENT.getFaces(raiseError=True, lunaRequestId=self.requestId)).json["count"]
        countPerson = (yield self.adminClient.getPersons(raiseError=True)).json["person_count"]
        countAccounts = (yield self.adminClient.getAccounts(raiseError=True)).json["account_count"]

        return {"person_count": countPerson, "descriptor_count": countDescriptors, "account_count": countAccounts,
                "accounts_list_count": countAccountLists}
