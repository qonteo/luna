from common.queue import BaseQueue, Consumer
from tornado import gen
from analytics.common_objects import logger
from analytics.common_objects import timer
from analytics.workers.lps_check_person_quality import calculateHitTopNListPersonProbability
from analytics.workers.cluster_worker import cluster_worker
from analytics.workers.linker_worker import rootLinker
from analytics.workers.cross_matchig import crossMatch
from analytics.workers.reporter_worker import reporter_worker
from functools import wraps
from errors.error import Result, Error
from analytics.workers.tasks_functions import flushFailedTask
from app.common_objects import API_VERSION


def taskExceptionWrap(func):
    """
    Decorator for catching exceptions in processing task.

    :param func: decorated function
    :return: if exception was caught task would be mark as failed.
    """

    @wraps(func)
    @gen.coroutine
    def wrap(self, *func_args, **func_kwargs):
        try:
            res = yield func(self, *func_args, **func_kwargs)
            return res
        except Exception:
            logger.exception(func.__qualname__)
            taskId = func_args[0].id
            logger.error("Uncaught exception in task {}".format(taskId))
            yield flushFailedTask(func_args[0], Result(Error.UncaughtTaskException, 0),
                                  "/api/{}/analytics/tasks/{}".format(API_VERSION, taskId))
            return Result(Error.ElasticRequest, 500)

    return wrap


class HitTopNWorker(Consumer):
    """
    The Hit Top N queue worker.
    """
    @timer.timerTor
    @taskExceptionWrap
    @gen.coroutine
    def f(self, task):
        logger.debug("Task {} started".format(task.id))
        yield calculateHitTopNListPersonProbability(task)
        logger.debug("Task {} ended".format(task.id))


class LinkerWorker(Consumer):
    """
    The Linker queue worker.
    """
    @timer.timerTor
    @taskExceptionWrap
    @gen.coroutine
    def f(self, task):
        logger.debug("Task {} started".format(task.id))
        yield rootLinker(task)
        logger.debug("Task {} ended".format(task.id))


class ClusterizationWorker(Consumer):
    """
    The Clusterization queue worker.
    """
    @timer.timerTor
    @taskExceptionWrap
    @gen.coroutine
    def f(self, task):
        logger.debug("Task {} started".format(task.id))
        yield cluster_worker(task)
        logger.debug("Task {} ended".format(task.id))


class CrossMatcherWorker(Consumer):
    """
    The Cross-matching queue worker.
    """
    @timer.timerTor
    @taskExceptionWrap
    @gen.coroutine
    def f(self, task):
        logger.debug("Task {} started".format(task.id))
        yield crossMatch(task)
        logger.debug("Task {} ended".format(task.id))


class ReporterWorker(Consumer):
    """
    The Reporter queue worker.
    """
    @timer.timerTor
    @gen.coroutine
    def f(self, task):
        logger.debug("Task {} started".format(task.id))
        yield reporter_worker(task)
        logger.debug("Task {} ended".format(task.id))


HIT_TOP_QUEUE = BaseQueue(HitTopNWorker, 5, logger)
LINKER_QUEUE = BaseQueue(LinkerWorker, 5, logger)
CLUSTERIZATION_QUEUE = BaseQueue(ClusterizationWorker, 5, logger)
CROSS_MATCHER_QUEUE = BaseQueue(CrossMatcherWorker, 5, logger)
REPORTER = BaseQueue(ReporterWorker, 5, logger)
