# -*- coding: utf-8 -*-
import asyncio

from tornado.platform.asyncio import AnyThreadEventLoopPolicy

from app.app import application
from app.check_connection import checkConnections
from tornado import httpserver
from tornado.ioloop import IOLoop
from configs.comand_line_args_parser import getOptionsParser


if __name__ == "__main__":
    if checkConnections():
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
        cmdOptions = getOptionsParser()
        http_server = httpserver.HTTPServer(application)
        http_server.bind(cmdOptions["port"])
        http_server.start(cmdOptions["workers"])
        IOLoop.configure('tornado.platform.asyncio.AsyncIOLoop')
        IOLoop.current().start()
    else:
        print("check connection fail, close app")
