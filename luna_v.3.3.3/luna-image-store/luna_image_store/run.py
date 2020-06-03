# -*- coding: utf-8 -*-
import asyncio

from tornado import httpserver
from tornado.ioloop import IOLoop
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

from configs.comand_line_args_parser import getOptionsParser
from app.check_connection import checkConnections


if __name__ == "__main__":

    if checkConnections():
        from app.app import application

        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
        cmdOptions = getOptionsParser()
        http_server = httpserver.HTTPServer(application)
        http_server.bind(cmdOptions["port"])
        http_server.start(cmdOptions["workers"])
        IOLoop.configure('tornado.platform.asyncio.AsyncIOLoop')
        print("Service start on {} port, worker count {}".format(cmdOptions["port"], cmdOptions["workers"]))
        IOLoop.current().start()
    else:
        print("check connection fail, close app")
