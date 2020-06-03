from tornado import gen

from app.handlers.temlate_base_handler import TemplateBaseHandler


class TemplateGrafanaHandler(TemplateBaseHandler):

    @TemplateBaseHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        grafana = (yield self.adminClient.getGrafana(raiseError=True)).json
        return self.render("templates/grafana_frame.html", grafana=grafana["grafana_url"] + "/?orgId=1")
