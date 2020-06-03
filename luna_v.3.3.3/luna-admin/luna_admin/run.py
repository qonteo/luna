"""
Module run backend and tasks services.

Example:
    Run services:

        literal blocks::
            $ python run.py --config=./configs/myconf.conf --service_type=admin_task
            $ python run.py --config=./configs/myconf.conf --service_type=admin_backend

    Get help:
        literal blocks::
            $ python run.py --help
"""
import asyncio

from tornado import httpserver
from tornado.ioloop import IOLoop
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

from app.handlers.app import application
from app.check_connection import checkConnections
from configs.comand_line_args_parser import getOptionsParser
from task_workers.handlers.app import task_application

if __name__ == "__main__":
    if checkConnections():
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

        cmdOptions = getOptionsParser()

        if cmdOptions["service_type"] == "admin_backend":
            http_server = httpserver.HTTPServer(application)
            http_server.bind(cmdOptions["back_port"])
        elif cmdOptions["service_type"] == "admin_task":
            http_server = httpserver.HTTPServer(task_application)
            http_server.bind(cmdOptions["task_port"])
        else:
            print("parameter 'service_type' is not set or wrong")
            cmdOptions.print_help()
            exit(2)
        http_server.start(cmdOptions["workers"])
        IOLoop.current().start()

    else:
        print("check connection fail, close app")
        exit(1)
