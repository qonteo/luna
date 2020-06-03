from tornado import gen

from app.handlers.temlate_base_handler import TemplateBaseHandler
from common.pagging import getPages
from crutches_on_wheels.errors.errors import Error


class TemplateTasksViewHandler(TemplateBaseHandler):

    @TemplateBaseHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        return self.render("templates/gc_stats.html")


class TemplateTasksHandler(TemplateBaseHandler):

    @TemplateBaseHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):

        page, pageSize = self.getPagination()
        taskType = self.getQueryParam("task_type")
        tasks = (yield self.adminClient.getTasks(taskType,pageSize, pageSize, raiseError=True)).json
        pages = getPages(page, pageSize, tasks["task_count"])
        if taskType == "reextract":
            return self.render("templates/gc_re_extract_tabel.html", **tasks["tasks"], **pages)
        else:
            return self.render("templates/gc_re_extract_tabel.html", **tasks["tasks"], **pages)