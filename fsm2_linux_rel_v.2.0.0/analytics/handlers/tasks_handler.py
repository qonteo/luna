from analytics.handlers.base_handler import BaseHandler, coRequestExeptionWrap
from errors.error import Error
from tornado import web, gen, escape
from analytics.common_objects import logger, ES_CLIENT
from common.tasks import Task, TaskType
from analytics.queue.tasks_queue import HIT_TOP_QUEUE, LINKER_QUEUE, CROSS_MATCHER_QUEUE, CLUSTERIZATION_QUEUE, REPORTER
from common.switch import switch


class TasksHandler(BaseHandler):
    """
    The only analytics handler. Used to receive tasks.
    """
    @web.asynchronous
    @coRequestExeptionWrap
    @gen.coroutine
    def post(self):
        """
        A task start handler. Add a received task to one of queues chosen by task type.

        :return: None
        """
        task = escape.json_decode(self.request.body)
        logger.info("Receive task {}".format(task["task_id"]))
        res = yield ES_CLIENT.getTask(task["task_id"])
        if res.fail:
            logger.error("failed to get task {}, reason {}".format(task["task_id"], res.description))
            return self.error(500, res.errorCode, res.description)
        else:
            task = Task.generateTaskFromDict(res.value)
            for case in switch(task.type):
                if case(TaskType.HIT_TOP_N):
                    yield HIT_TOP_QUEUE.putTask(task)
                    break
                if case(TaskType.CLUSTERIZATION):
                    yield CLUSTERIZATION_QUEUE.putTask(task)
                    break
                if case(TaskType.LINKER):
                    yield LINKER_QUEUE.putTask(task)
                    break
                if case(TaskType.CROSS_MATCHER):
                    yield CROSS_MATCHER_QUEUE.putTask(task)
                    break
                if case(TaskType.REPORTER):
                    yield REPORTER.putTask(task)
                    break
            else:
                return self.error(400, Error.UnknownTaskType.getErrorCode(),
                                  Error.UnknownTaskType.getErrorDescription())
        return self.success(201, {"detail": "success"})
