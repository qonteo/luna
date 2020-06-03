from tornado import web, gen

from app.common_objects import ES_CLIENT as es
from app.handlers.base_handler import BaseHandler, coRequestExeptionWrap
from common.helpers import ifInt, ifFloat, ifTime, ifUUID, ifUUIDs, ifGroupBy, compileTime, \
    replaceTimeRecursively
from errors.error import Error
from .handler_functions import compressFilters, validateParams, compileParams, validateStatParams

# dict has format {"<query param name>": (<validator>, <compiler>)}
searchSchema = {
    item[0]: {1: ((lambda x: True), (lambda x: x)), 2: item[1:]+((lambda x: x),), 3: item[1:]}[len(item)]
    for item in
    (
        ("page", ifInt, lambda x: max(1, int(x))),
        ("page_size", ifInt, lambda x: max(1, min(int(x), 100))),
        ("similarity__gt", ifFloat, lambda x: max(0, min(float(x), 1))),
        ("similarity__lt", ifFloat, lambda x: max(0, min(float(x), 1))),
        ("age__gt", ifFloat, lambda x: max(0, float(x))),
        ("age__lt", ifFloat, lambda x: max(0, float(x))),
        ("gender", ifInt, lambda x: max(0, min(int(x), 1))),
        ("create_time__gt", ifTime, compileTime),
        ("create_time__lt", ifTime, compileTime),
        ("user_data",),
        ("sim_descriptor", ifUUID),
        ("sim_person", ifUUID),
        ("sim_list", ifUUID),
        ("person_id", ifUUID),
        ("sim_user_data",),
        ("external_id", ifUUID),
        ("handler_ids", ifUUIDs, lambda x: x.split(',')),
        ("sources", lambda x: x, lambda x: x.split(',')),
        ("tags", lambda x: True, lambda x: x.split(',')),
    )
}
# dict has format {"<query param name>": (<validator>, <compiler>)}
aggregateSchema = {
    **searchSchema,
    **{
        item[0]: item[1:] + ((lambda x: x),)
        for item in
        (
            ("aggregator", lambda t: t in ['count', 'min', 'max', 'avg']),
            ("group_by", ifGroupBy),
            ("target", lambda t: t in ['age', 'gender']),
        )
    }
}

# merge range filters from compiled query params tuple
compressSchema = (
    ("create_time", ("create_time__gt", "create_time__lt")),
    ("age", ("age__gt", "age__lt")),
    ("similarity", ("similarity__gt", "similarity__lt")),
)


class GroupHandler(BaseHandler):
    """
    Group handler.
    """
    @web.asynchronous
    @coRequestExeptionWrap
    @gen.coroutine
    def get(self, groupId):
        """
        Get group by its id.
        Response status codes:
            200 if event was found
            404 if event was not found
            500 if internal system error occurred

        :param groupId: a group id
        :return: None
        """
        groupRes = yield es.getGroup(groupId)
        if groupRes.fail:
            if groupRes.error == Error.GroupNotFound:
                return self.error(404, groupRes.errorCode, groupRes.description)
            return self.error(500, groupRes.errorCode, groupRes.description)
        self.success(200, replaceTimeRecursively(groupRes.value))


class GroupsHandler(BaseHandler):
    """
    Groups search handler.
    """
    @web.asynchronous
    @coRequestExeptionWrap
    @gen.coroutine
    def get(self):
        """
        Search groups by filters listed in searchSchema.keys().
        Response status codes:
            200 if search succeed
            400 if request query parameters have wrong values
            500 if internal system error occurred

        :return: None
        """
        validateRes = validateParams(self.get_query_argument, searchSchema)
        if validateRes.fail:
            return self.error(400, validateRes.error.getErrorCode(),
                              validateRes.error.getErrorDescription())

        filters = compileParams(self.get_query_argument, searchSchema)
        compressFilters(filters, compressSchema)

        searchFilter = es.SearchGroup(**filters)
        searchRes = yield es.searchGroups(searchFilter)
        if searchRes.fail:
            return self.error(500, searchRes.error_code, searchRes.description)
        return self.success(200, searchRes.value)


class GroupsStatsHandler(BaseHandler):
    """
    Groups statistic handler.
    """
    @web.asynchronous
    @coRequestExeptionWrap
    @gen.coroutine
    def get(self):
        """
        Search groups by filters and aggregations listed in aggregateSchema.keys().
        Response status codes:
            200 if stat request succeed
            400 if request query parameters have wrong values
            500 if internal system error occurred

        :return: None
        """
        validateRes = validateStatParams(self.get_query_argument, aggregateSchema)
        if validateRes.fail:
            return self.error(400, validateRes.error.getErrorCode(),
                              validateRes.error.getErrorDescription())

        filters = compileParams(self.get_query_argument, aggregateSchema)
        compressFilters(filters, compressSchema)

        searchFilter = es.SearchGroup(**filters)
        searchRes = yield es.searchGroups(searchFilter)
        if searchRes.fail:
            return self.error(500, searchRes.errorCode, searchRes.description)
        return self.success(200, searchRes.value)
