from tornado import gen

from app.handlers.temlate_base_handler import TemplateBaseHandler
from crutches_on_wheels.errors.errors import Error


class TemplateVersionHandler(TemplateBaseHandler):

    @TemplateBaseHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):

        version = (yield self.adminClient.getVersion(raiseError=True)).json
        return self.render("templates/version.html", version=version["Version"])

