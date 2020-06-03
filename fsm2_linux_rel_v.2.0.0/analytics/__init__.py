import tornado
from tornado import web
from analytics.handlers.error_handler import ErrorHandler404
from analytics.handlers.tasks_handler import TasksHandler

settings = {}
UUID4_REGEXP = "[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"

applicationA = tornado.web.Application([
(r"/tasks", TasksHandler),

], default_handler_class=ErrorHandler404, **settings)



