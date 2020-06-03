import tornado

from task_workers.handlers.task_handler import TaskHandler

task_application = tornado.web.Application([(r"/task", TaskHandler),])