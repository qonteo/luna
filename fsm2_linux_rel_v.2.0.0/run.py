# -*- coding: utf-8 -*-
import asyncio
from tornado import httpserver
from tornado import ioloop
from tornado.ioloop import IOLoop
#from tornado.platform.asyncio import AnyThreadEventLoopPolicy

from app import application as eventsApp
from analytics import applicationA as analyticsApp
from app.classes.groups import periodicCleanGroups
from configs.comand_line_args_parser import getOptionsParser
from multiprocessing import Process
from common.check_environment import checkEnvironment


def runEvents(eventsApp, port):
    """
    Run events processing module.

    :param eventsApp: events processing module application
    :param port: start application port
    :return: None
    """
    #asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
    eventsServer = httpserver.HTTPServer(eventsApp)
    eventsServer.listen(port)
    ioloop.PeriodicCallback(periodicCleanGroups, 10000).start()
    IOLoop.current().start()


def runAnalytics(analyticsApp, port, countWorkers):
    """
    Run analytics module.

    :param analyticsApp: analytics module application
    :param port: start application port
    :param countWorkers: subprocess count to run
    :return: None
    """
    #asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
    analyticsServer = httpserver.HTTPServer(analyticsApp)
    analyticsServer.bind(port)
    analyticsServer.start(countWorkers)

    IOLoop.current().start()


if __name__ == "__main__":
    checkEnvironment()
    cmdOptions = getOptionsParser()
    processForEvents = Process(target = runEvents, args = (eventsApp, cmdOptions["events_port"]))
    processForTasks = Process(target = runAnalytics, args = (analyticsApp, cmdOptions["analytics_port"], 1))
    processForEvents.start()
    processForTasks.start()
    processForEvents.join()
