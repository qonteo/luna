from tornado import gen

from app.handlers.base_handler import BaseHandlerWithAuth
from app.handlers.temlate_base_handler import TemplateBaseHandler


class TemplateLoginHandler(TemplateBaseHandler):

    @BaseHandlerWithAuth.requestExceptionWrap
    @gen.coroutine
    def prepare(self):
        pass

    @TemplateBaseHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        self.render("templates/login_form.html")
