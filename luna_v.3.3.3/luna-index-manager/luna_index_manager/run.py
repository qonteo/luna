# -*- coding: utf-8 -*-
"""Run service
"""
import asyncio
import pprint

from tornado.ioloop import IOLoop
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

from app.app import application
from app.check_connection import checkConnections
from app.global_workers import crawler, reloadIndexQueue, indexWorker
from app.task_status_check import checkTasksStatus
from configs.comand_line_args_parser import getOptionsParser
from configs.config import options
from workers.index_reload_worker import ReloadWorker

if __name__ == "__main__":
    cmdOptions = getOptionsParser()
    if checkConnections():
        checkTasksStatus()
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
        application.listen(cmdOptions["port"])
        ReloadWorker.forceReloadIndexes()
        crawler.startCrawling()
        IOLoop.current().add_callback(reloadIndexQueue.process)
        IOLoop.current().add_callback(indexWorker.createIndexLoop)
        print("Service start on {} port".format(cmdOptions["port"]))
        IOLoop.current().start()
    else:
        pp = pprint.PrettyPrinter(indent=4)
        cmdOptions.print_help()
        pp.pprint(options.as_dict())
