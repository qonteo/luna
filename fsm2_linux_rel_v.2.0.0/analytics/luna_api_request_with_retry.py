from tornado import gen
from analytics.common_objects import logger
from errors.error import Error, Result
from configs.config import MAX_TRY_COUNT


def generateError(luna_reply, msg):
    """
    Generate an error from the Luna API reply

    :param luna_reply: a Luna API failed reply
    :param msg: error message
    :return: result:
        Fail with an error occurred
    """
    logger.error("failed {}, reply: {}".format(msg, luna_reply.body))
    error = Error.generateLunaError(msg, luna_reply.body)
    return Result(error, luna_reply.body)


@gen.coroutine
def makeRequestToLunaApiWithRetry(request_function, error_msg, *args, **kwargs):
    """
    Make request to Luna API with retry.

    :param request_function: coroutine to start
    :param error_msg: message to print
    :param args: coroutine args
    :param kwargs: coroutine kwargs
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    error_reply = None
    for try_count in range(MAX_TRY_COUNT):

        reply = yield request_function(*args, **kwargs)
        if reply.success:
            return Result(Error.Success, reply.body)
        if reply.statusCode < 500:
            return generateError(reply, error_msg)
        error_reply = reply
        logger.error(
            "retry {}, try {}, luna api reply: {}".format(error_msg, try_count, reply.body))
    else:
        return generateError(error_reply, "{}, try {}".format(error_msg, MAX_TRY_COUNT))
