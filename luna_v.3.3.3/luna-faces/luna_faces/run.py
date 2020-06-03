# -*- coding: utf-8 -*-
import asyncio

from tornado import httpserver
from tornado.ioloop import IOLoop
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

from configs.comand_line_args_parser import getOptionsParser
from configs.config import options
import pprint
from app.handlers.app import application
from app.check_connection import checkConnections


if __name__ == "__main__":
    cmdOptions = getOptionsParser()
    if checkConnections():
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
        http_server = httpserver.HTTPServer(application)
        http_server.bind(cmdOptions["port"])
        http_server.start(cmdOptions["workers"])
        IOLoop.configure('tornado.platform.asyncio.AsyncIOLoop')
        IOLoop.current().start()
    else:
        pp = pprint.PrettyPrinter(indent = 4)
        cmdOptions.print_help()
        pp.pprint(options.as_dict())
