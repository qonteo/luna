from enum import Enum

from configs.config import ADMIN_STATISTICS_SERVER_ORIGIN, ADMIN_STATISTICS_DB
from tornado import gen
from tornado import httpclient
from tornado.httpclient import HTTPRequest
from crutches_on_wheels.errors.errors import Error


class StatsType(Enum):
    """
    Enum for stats types
    """

    ERRORS = "gc_errors"            #: error stats
    TASK_STATS = "task_stats"       #: task stats


def generateListAdminStatisticsRequestBody(gcListStats):
    influxRequest = "gc_lists"
    influxRequest += ",luna_list_count=" + str(gcListStats.countLunaList)
    influxRequest += " luna_list_count=" + str(gcListStats.countLunaList)
    influxRequest += ",request_time=" + str(gcListStats.requestTime)
    influxRequest += ",duplicate_error_count=" + str(gcListStats.duplicateErrorCount)
    influxRequest += ",non_attach_error_count=" + str(gcListStats.nonAttachErrorCount)
    return influxRequest


def generateErrorAdminStatisticsRequestBody(errorsStats):
    influxRequest = "gc_errors"
    influxRequest += ",error_code=" + str(errorsStats[1])
    influxRequest += ",target=" + str(errorsStats[2])
    influxRequest += " text=" + str(errorsStats[0])
    return influxRequest


def generateRemoveDescriptorsStats(stats):
    influxRequest = "gc_descriptors"
    influxRequest += ",luna_account_id=" + str(stats[0])
    influxRequest += " luna_descriptor_count=" + str(stats[1])
    influxRequest += ",luna_s3_error_count=" + str(stats[2])
    influxRequest += ",request_time=" + str(stats[3])
    return influxRequest


@gen.coroutine
def sendGCListsStats(stats, statsType, logger):
    if statsType == StatsType.ERRORS:
        influxRequest = generateErrorAdminStatisticsRequestBody(stats)
    else:
        influxRequest = generateRemoveDescriptorsStats(stats)

    requestListStatistics = HTTPRequest(ADMIN_STATISTICS_SERVER_ORIGIN + "/write?db=" + ADMIN_STATISTICS_DB,
                                        body=influxRequest,
                                        method="POST",
                                        headers={"Content-Type": "application/json"})
    http_client = httpclient.AsyncHTTPClient()
    reply = yield http_client.fetch(requestListStatistics, raise_error=False)
    if not (200 <= reply.code < 300):
        logger.error("failed send list stats, status code {}".format(reply.code))
