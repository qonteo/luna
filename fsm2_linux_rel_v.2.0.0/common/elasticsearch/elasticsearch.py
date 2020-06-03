from functools import wraps
from time import time

from tornado import gen, httpclient, escape, locks
from tornado.httpclient import HTTPRequest

from common.helpers import ifInt, getNowTimestampMillis, convertRfc3339ToTimestampMillis, convertTimestampMillisToRfc3339, \
    replaceTimeRecursively
from common.timer import Timer
from configs.config import ELASTICSEARCH_URL as ES_URL
from configs.config import GENDER_THRESHOLD, MAX_OBJECTS_TO_ATTACH
from errors.error import Error, Result

taskLock = locks.Lock()


def lockGuard(wrapFunc):
    """
    Lock guard for work with tasks correctly: not to update task while it is moving to done tasks.

    :param wrapFunc: func to wrap
    :return: wrapped func
    """
    @wraps(wrapFunc)
    @gen.coroutine
    def wrap(*func_args, **func_kwargs):
        with (yield taskLock.acquire()):
            res = yield wrapFunc(*func_args, **func_kwargs)
            return res

    return wrap


def makeFilter(k, v):
    """
    Make match filter.

    :param k: field name
    :param v: field value
    :return: es filter
    """
    return {"match": {k: v}}


def makeRangeFilter(k, v):
    """
    Make range filter.

    :param k: field name
    :param v: field boundaries
    :return: es filter
    """
    return {"range": {k: {
        **({'gte': v[0]} if v[0] is not None else {}),
        **({'lte': v[1]} if v[1] is not None else {})
    }}}


def makeTagFilter(k, v):
    """
    Make AND match filter.

    :param k: field name
    :param v: field values
    :return: es filter
    """
    return {"bool": {"filter": [{"match": {k: vi}} for vi in v]}}


def makeAntiTagFilter(k, v):
    """
    Make OR match filter.

    :param k: field name
    :param v: field values
    :return: es filter
    """
    return {"bool": {"should": [{"match": {k: vi}} for vi in v]}}


def makeMissFilter(k, v):
    """
    Make NOT_EXIST field filter.

    :param k: field name
    :param v: <garbage>
    :return: es filter
    """
    return {"bool": {"must_not": {"exists": {"field": k}}}}


def elasticRequestExceptionWrap(func):
    """
    Decorator for catching exceptions in request to es.

    :param func: decorated function
    :return: if exception was caught, system calls error method with error code ElasticRequest
    """
    @wraps(func)
    @gen.coroutine
    def wrap(self, *func_args, **func_kwargs):
        try:
            res = yield func(self, *func_args, **func_kwargs)
            return res
        except Exception as e:
            self.logger.exception(func.__qualname__ )
            return Result(Error.ElasticRequest, 500)

    return wrap


def esTimer(func):
    """
    Decorator for asynchronous function work time estimation.

    :param func: decorated function
    """
    @wraps(func)
    @gen.coroutine
    def wrap(self, *func_args, **func_kwargs):
        if __debug__:
            start = time()
            res = yield func(self, *func_args, **func_kwargs)
            end = time()
            self.logger.debug(func.__qualname__ + " time: " + str(round(end - start, 5)))
            return res
        else:
            res = yield func(self, *func_args, **func_kwargs)
            return res

    return wrap


def prettyReply(reply):
    """
    Make pure data from reply.

    :param reply: an es reply object
    :return: result json
    """
    decoded = escape.json_decode(reply.body)
    return {"total": decoded['hits']['total'], 'hits': [h['_source'] for h in decoded['hits']['hits']]}


def prettySearch(reply):
    """
    Make pure data from search reply.

    :param reply: an es search reply object
    :return: result json
    """
    decoded = escape.json_decode(reply.body)
    if 'aggregations' in decoded:
        res = decoded['aggregations']['level_one']['buckets']
        if len(res):
            if 'level_two' in res[0]:
                def value(r):
                    """
                    Return pure data from second-level aggregation.

                    :param r: every result
                    :return: result value
                    """
                    return r['level_two']['value']
            else:
                def value(r):
                    """
                    Return documents count if there is no second-level aggregation.

                    :param r: every result
                    :return: result value
                    """
                    return r['doc_count']

            def key(r):
                """
                Return "key" if "key_as_string" does not exist.

                :param r: every result
                :return: result key
                """
                if isinstance(r['key'], str):
                    return r['key']
                else:
                    return convertTimestampMillisToRfc3339(r['key'])

            sortKey = (lambda r: int(r[0])) if ifInt(key(res[0])) else (lambda r: r[0])
            res = {'total': len(res), 'hits': sorted([(key(r), value(r)) for r in res], key=sortKey)}
        else:
            res = {'total': 0, 'hits': res}
    else:
        res = replaceTimeRecursively(prettyReply(reply))
    return res


class Elasticsearch:
    """
    Elasticsearch database client.

    Attributes:
        logger (Logger): logger to log messages
        timer (Timer): timer to measure duration of function performance
    """
    logger = None

    def __init__(self, logger):
        """
        :param logger: logger to log
        """
        self.logger = logger
        self.timer = Timer(self.logger)

    class SearchBase:
        """
        Search base class
        """
        aggregator = None
        group_by = None
        target = None
        alias = {}
        nested = []
        page = 1
        page_size = 20

        @classmethod
        def make_nested(cls, pre_filters, nested_fields=None):
            """
            Make nested filters if needed.
            If we need to filter nested objects in es, we should make nested query.
            For example:
                If we have an object:
                    {
                    "name": "Dona",
                    "address": [
                            {
                                "country": "United Arab Emirates",
                                "city": "Abudabi"
                            },
                            {
                                "country": "USA",
                                "city": "Moscow"
                            }
                        ]
                    }
                We need to query people from "country": "USA" and "city": "Abudabi" (listed in the nested object)
                    and not to query people like Dona.
                To make this work we use nested queries.

            :param pre_filters: filters to make nested if needed
            :param nested_fields: nested object address list
            :return: made nested filters
            """
            def go(place: dict, plan: str) -> dict:
                """
                Defaultdict emulation.

                :param place: dictionary to start
                :param plan: dot-separated depth path
                :return: last created dict
                """
                for step in plan.split('.'):
                    if step not in place:
                        place[step] = {}
                    place = place[step]
                return place

            def get_key(place):
                """
                Returns first key from dict.

                :param place: dict to get the first key
                :return: first key
                """
                return next(iter(place))

            def go_nested(place):
                """
                Get first nested object from dict.

                :param place: dict
                :return: nested object
                """
                return place[get_key(place)]

            if nested_fields is None:
                nested_fields = cls.nested

            filters = []
            for nested in nested_fields:
                filters_to_nested = []
                for f in pre_filters:
                    if nested in get_key(go_nested(f)):
                        filters_to_nested += [f]

                if len(filters_to_nested):
                    nested_result = {}
                    go(nested_result, 'nested.query.bool')['filter'] = filters_to_nested
                    nested_result['nested']['path'] = nested

                    [pre_filters.remove(f) for f in filters_to_nested]

                    filters += [nested_result]

                    # make recursive for nested -> nested format
                    nested_bool = go(nested_result, 'nested.query.bool')
                    new_nested_fields = [n for n in nested_fields if n != nested]
                    nested_bool['filter'] = cls.make_nested(nested_bool['filter'], new_nested_fields)
            filters += pre_filters
            return filters

        @property
        def query(self):
            """
            Make query from the object attributes.

            :return: json query as dict
            """
            def validated(f):
                """
                Shows if filter is not empty.

                :param f: filter name
                :return: True if to use filter, False if not
                """
                return f in self.alias and self.__dict__[f] is not None and self.__dict__[f] != (None, None)

            time_field = "create_time"

            filters = self.make_nested([
                self.alias[e][1](self.alias[e][0], self.__dict__[e])
                for e in self.__dict__
                if validated(e)
            ])

            if self.aggregator is None:
                aggregations = {}
            else:
                aggregations = {"aggs": {"level_one": {}}}

                if self.group_by in ["monthOfYear", "dayOfYear", "dayOfMonth", "dayOfWeek", "hourOfDay", "minuteOfDay"]:
                    aggregations["aggs"]["level_one"]["terms"] = {
                        "script": "doc['{}'].date.{}".format(
                            time_field,
                            self.group_by
                        ),
                        "size": 100000
                    }
                else:
                    aggregations["aggs"]["level_one"]["date_histogram"] = {
                        "field": time_field,
                        "interval": self.group_by
                    }

                if not self.aggregator == 'count':
                    aggregations['aggs']['level_one']['aggs'] = {'level_two': {self.aggregator: {
                        "field": self.alias[self.target][0]
                    }}}
            return {
                "size": self.page_size,
                "from": (self.page - 1) * self.page_size,
                **({"sort": [
                    {time_field: "desc"}
                ]} if not aggregations else {"size": 0}),

                "query": {"bool": {"filter": filters}},
                **aggregations
            }

    class SearchEvent(SearchBase):
        """
        Search or get statistics on events.

        Attributes:
            page_size (int): number of results in page
            page (int): results page number
            create_time (tuple): range event create time
            age (tuple): range event age
            gender (tuple): range event gender
            similarity (tuple): range event similarity
            sim_descriptor (UUID4): descriptor id event was matched with
            sim_person (UUID4): person id an event was matched with
            sim_list (UUID4): Luna API list event was matched
            group_id (UUID4): group id an event is in
            person_id (UUID4): person id the event descriptor is in
            user_data (str): person user_data the event descriptor is in
            sim_user_data (str): person user_data an event was matched with
            external_id (str): event external id
            handler_ids (list of UUID4): handler ids events were proceed with
            sources (list): event sources
            tags (list): event tags
            aggregator (str): aggregator if we make statistic request
            target (str): target field to aggregate ("age" or "gender")
            group_by (str): group by aggregation (time period or special one)
        """
        alias = {
            "create_time": ("create_time", makeRangeFilter),
            "sim_descriptor": ("search.candidates.descriptor_id", makeFilter),
            "sim_person": ("search.candidates.person_id", makeFilter),
            "sim_list": ("search.list_id", makeFilter),
            "sim_user_data": ("search.candidates.user_data", makeFilter),
            "similarity": ("search.candidates.similarity", makeRangeFilter),
            "age": ("extract.attributes.age", makeRangeFilter),
            "gender": ("extract.attributes.gender", makeRangeFilter),
            "person_id": ("person_id", makeFilter),
            "group_id": ("group_id", makeFilter),
            "user_data": ("user_data", makeFilter),
            "external_id": ("external_id", makeFilter),
            "handler_ids": ("handler_id", makeAntiTagFilter),
            "sources": ("source", makeAntiTagFilter),
            "tags": ("tags", makeTagFilter),
        }
        # order is important
        nested = ["search", "search.candidates"]

        def __init__(self,
                     page_size=20, page=1,
                     create_time=(None, None), age=(None, None), gender=(None, None), similarity=(None, None),
                     sim_descriptor=None, sim_person=None, sim_list=None, group_id=None, person_id=None,
                     user_data=None, sim_user_data=None, external_id=None,
                     handler_ids=None, sources=None, tags=None,
                     aggregator=None, target=None, group_by=None
                     ):
            """
            :param page_size: number of results in page
            :param page: results page number
            :param create_time: range event create time
            :param age: range event age
            :param gender: range event gender
            :param similarity: range event similarity
            :param sim_descriptor: descriptor id event was matched with
            :param sim_person: person id an event was matched with
            :param sim_list: Luna API list event was matched
            :param group_id: group id an event is in
            :param person_id: person id the event descriptor is in
            :param user_data: person user_data the event descriptor is in
            :param sim_user_data: person user_data an event was matched with
            :param external_id: event external id
            :param handler_ids: handler ids events were proceed with
            :param sources: event sources
            :param tags: event tags
            :param aggregator: aggregator if we make statistic request
            :param target: target field to aggregate ("age" or "gender")
            :param group_by: group by aggregation (time period or special one)
            """
            self.page_size = page_size
            self.page = page

            self.create_time = create_time
            self.age = age

            if gender == 1:
                gender = (GENDER_THRESHOLD, None)
            elif gender == 0:
                gender = (None, GENDER_THRESHOLD)
            self.gender = gender

            self.similarity = similarity

            self.sim_descriptor = sim_descriptor
            self.sim_person = sim_person
            self.group_id = group_id
            self.person_id = person_id
            self.sim_list = sim_list
            self.user_data = user_data
            self.sim_user_data = sim_user_data
            self.external_id = external_id

            self.handler_ids = handler_ids
            self.sources = sources
            self.tags = tags

            self.aggregator = aggregator
            self.target = target
            self.group_by = group_by

    class SearchGroup(SearchBase):
        """
        Search or get statistic on groups.

        Attributes:
            page_size (int): number of results in page
            page (int): results page number
            age (tuple): range group age
            gender (tuple): range group gender
            similarity (tuple): range group similarity
            create_time (tuple): range group create time
            external_id (str): external id group
            sim_descriptor (UUID4): descriptor id group events was matched with
            sim_person (UUID4): person id group events was matched with
            sim_list (UUID4): Luna API list group events were matched
            sim_user_data (str): person user_data group events was matched with
            person_id (UUID4): group person id
            handler_ids (list of UUID4): handler ids groups are created on
            sources (list): group sources
            tags (list): group tags
            aggregator (str): aggregator if we make statistic request
            target (str): target field to aggregate ("age" or "gender")
            group_by (str): group by aggregation (time period or special one)
        """
        alias = {
            "age": ('attributes.age', makeRangeFilter),
            "gender": ('attributes.gender', makeRangeFilter),
            "similarity": ('search.candidate.similarity', makeRangeFilter),
            "sim_descriptor": ('search.candidate.descriptor_id', makeFilter),
            "sim_person": ('search.candidate.person_id', makeFilter),
            "sim_list": ("search.list_id", makeFilter),
            "sim_user_data": ('search.candidate.user_data', makeFilter),
            "handler_ids": ('handler_id', makeAntiTagFilter),
            "sources": ('source', makeAntiTagFilter),
            "tags": ('tags', makeTagFilter),
            "external_id": ('external_tracks_id', makeFilter),
            "person_id": ('person_id', makeFilter),
            "create_time": ('create_time', makeRangeFilter)
        }
        nested = ['search', 'search.candidate']

        def __init__(self,
                     page_size=20, page=1,
                     age=(None, None), gender=(None, None), similarity=(None, None), create_time=(None, None),
                     external_id=None, sim_descriptor=None, sim_person=None, sim_list=None, sim_user_data=None, person_id=None,
                     handler_ids=None, sources=None, tags=None,
                     aggregator=None, target=None, group_by=None
                     ):
            """
            :param page_size: number of results in page
            :param page: results page number
            :param age: range group age
            :param gender: range group gender
            :param similarity: range group similarity
            :param create_time: range group create time
            :param external_id: external id group
            :param sim_descriptor: descriptor id group events was matched with
            :param sim_person: person id group events was matched with
            :param sim_list: Luna API list group events were matched
            :param sim_user_data: person user_data group events was matched with
            :param person_id: group person id
            :param handler_ids: handler ids groups are created on
            :param sources: group sources
            :param tags: group tags
            :param aggregator: aggregator if we make statistic request
            :param target: target field to aggregate ("age" or "gender")
            :param group_by: group by aggregation (time period or special one)
            """
            self.page_size = page_size
            self.page = page

            self.age = age

            if gender == 1:
                gender = (GENDER_THRESHOLD, None)
            elif gender == 0:
                gender = (None, GENDER_THRESHOLD)
            self.gender = gender

            self.similarity = similarity
            self.create_time = create_time

            self.external_id = external_id
            self.sim_descriptor = sim_descriptor
            self.sim_person = sim_person
            self.sim_list = sim_list
            self.sim_user_data = sim_user_data
            self.person_id = person_id

            self.handler_ids = handler_ids
            self.sources = sources
            self.tags = tags

            self.aggregator = aggregator
            self.target = target
            self.group_by = group_by

    class SearchTask(SearchBase):
        """
        Search tasks.

        Attributes:
            inDone (bool): search done tasks or not
            page_size (int): number of results in page
            page (int): results page number
            create_time (tuple): range task create time
            task_type (str): task type ('hit_top_n', 'clusterization', 'linker', 'cross_matcher' or 'reporter')
            status (str): task status
            description (str): task description
        """
        alias = {
            "create_time": ('create_time', makeRangeFilter),
            "task_type": ("type", makeFilter),
            "status": ("status", makeFilter),
            "description": ("task.description", makeFilter),
            "location": ("Location", makeMissFilter)
        }

        def __init__(self,
                     inDone,
                     page_size=20, page=1,
                     create_time=(None, None),
                     task_type=None, status=None, description=None
                     ):
            """
            :param inDone: search done tasks or not
            :param page_size: number of results in page
            :param page: results page number
            :param create_time: range task create time
            :param task_type: task type ('hit_top_n', 'clusterization', 'linker', 'cross_matcher' or 'reporter')
            :param status: task status
            :param description: task description
            """
            self.inDone = inDone

            self.page_size = page_size
            self.page = page

            self.create_time = create_time

            self.task_type = task_type
            self.status = status
            self.description = description

    @gen.coroutine
    def makeRequest(self, url, method, body=None, headers=None):
        """
        Make request to the es.

        :param url: es path to make request
        :param method: request method
        :param body: request body
        :param headers: request headers
        :return: response
        """
        http_client = httpclient.AsyncHTTPClient()
        request = HTTPRequest("{}{}".format(ES_URL, url),
                              method=method,
                              headers=headers,
                              body=body,
                              allow_nonstandard_methods=True)
        res = yield http_client.fetch(request, raise_error=False)
        return res

    def makeResult(self, reply, special=None):
        """
        Status code resolver.

        :param reply: reply to process
        :param special: special code->lambda result generator
        :return: result:
            Success if reply.code is success (>=200 and <300) or special if provided
            Fail with corresponding error if reply.code is not success (>=400) or special if provided
        """
        if reply.code >= 300:
            self.logger.debug("ELASTIC {}: {}".format(reply.code, reply.body))
        if special is not None:
            for code, result in special.items():
                if reply.code == code:
                    return Result(**result())

        if 200 <= reply.code < 300:
            return Result(Error.Success, reply.body.decode())
        if reply.code == 403:
            return Result(Error.generateError(
                Error.ElasticInternal,
                'Forbidden. Check Elasticsearch node configuration.'
            ), reply.body.decode())
        if reply.code == 404:
            return Result(Error.ElasticNotFound, reply.body.decode())
        if reply.code == 405:
            return Result(Error.generateError(Error.ElasticInternal, "Method Not Allowed."), reply.body.decode())
        if 400 <= reply.code < 500:
            return Result(Error.ElasticMalformedRequest, reply.body.decode())
        self.logger.error("ELASTIC {}: {}".format(reply.code, reply.body))
        if reply.code == 599:
            if reply.error.message == 'Timeout during request':
                return Result(Error.ElasticTimeout, 0)
            return Result(Error.ElasticServiceUnavailable, 0)
        if 500 <= reply.code:
            return Result(Error.ElasticInternal, reply.body.decode())
        return Result(Error.UnknownError, (reply.code, reply.body.decode()))

    @elasticRequestExceptionWrap
    @esTimer
    @gen.coroutine
    def putEvent(self, event):
        """
        Put event.

        :param event: event ot put
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        eventId = event.id
        reply = yield self.makeRequest("/events/doc/{}".format(eventId), "PUT", event.json,
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply)

    @elasticRequestExceptionWrap
    @gen.coroutine
    def getEvent(self, eventId):
        """
        Get an event by id.

        :param eventId: event id
        :return: result:
            Success with the event if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/events/doc/{}/_source".format(eventId), "GET")
        return self.makeResult(reply, {
            404: lambda: {"error": Error.EventNotFound, "value": reply.body.decode("utf-8")},
            200: lambda: {"error": Error.Success, "value": escape.json_decode(reply.body)}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def searchEvents(self, searchEvent: SearchEvent):
        """
        Search or aggregate events.

        :param searchEvent: SearchEvent object
        :return: result:
            Success with a search result if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/events/doc/_search", "POST", escape.json_encode(searchEvent.query),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            200: lambda: {"error": Error.Success, "value": prettySearch(reply)}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def addListDescriptorsToEvent(self, eventId, listId):
        """
        Add a Luna API descriptor list to the event.

        :param eventId: the event id to add to
        :param listId: a lLuna API list id to add
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        payload = {
            "script": {
                "source": "ctx._source['descriptors_lists'].add('{}')".format(listId)
            }
        }
        reply = yield self.makeRequest("/events/doc/{}/_update".format(eventId), "POST", escape.json_encode(payload),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            404: lambda: {"error": Error.EventNotFound, "value": reply.body.decode()}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def addListPersonsToEvent(self, eventId, listId):
        """
        Add a Luna API person list to the event.

        :param eventId: the event id to add to
        :param listId: a lLuna API list id to add
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        payload = {
            "script": {
                "source": "ctx._source['persons_lists'].add('{}')".format(listId)
            }
        }
        reply = yield self.makeRequest("/events/doc/{}/_update".format(eventId), "POST", escape.json_encode(payload),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            404: lambda: {"error": Error.EventNotFound, "value": reply.body.decode()}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def updateGroupIdInEvent(self, eventId, groupId):
        """
        Update group id in the event.

        :param eventId: the event id
        :param groupId: group id to update
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        payload = {"doc": {
            'group_id': groupId
        }}
        reply = yield self.makeRequest("/events/doc/{}/_update".format(eventId), "POST", escape.json_encode(payload),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            404: lambda: {"error": Error.EventNotFound, "value": reply.body.decode("utf-8")}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def updatePersonInEvent(self, eventId, personId):
        """
        Update a person id in the event.

        :param eventId: the event id
        :param personId: a person id
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        payload = {"doc": {
            'person_id': personId,
        }}
        reply = yield self.makeRequest("/events/doc/{}/_update".format(eventId), "POST", escape.json_encode(payload),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            404: lambda: {"error": Error.GroupNotFound, "value": reply.body.decode("utf-8")}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def getHandlers(self, page_size, page, nameStartsWith=None):
        """
        Get handlers by name with pagination.

        :param page_size: number of results in page
        :param page: results page number
        :param nameStartsWith: name prefix (or full name)
        :return: result:
            Success with a search result if succeed
            Fail if an error occurred
        """
        payload = {"size": page_size, "from": (page - 1) * page_size}
        if nameStartsWith is not None:
            payload.update({"query": {"match_phrase_prefix": {"name": nameStartsWith}}})
        reply = yield self.makeRequest("/handlers/doc/_search", "POST", escape.json_encode(payload),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            200: lambda: {"error": Error.Success, "value": prettyReply(reply)}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def getHandler(self, handlerId):
        """
        Get handler by id.

        :param handlerId: the handler id
        :return: result:
            Success with a handler if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/handlers/doc/{}/_source".format(handlerId), "GET")
        return self.makeResult(reply, {
            404: lambda: {"error": Error.HandlerNotFound, "value": reply.body.decode("utf-8")},
            200: lambda: {"error": Error.Success, "value": escape.json_decode(reply.body)},
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def putHandler(self, handler):
        """
        Put handler.

        :param handler:
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/handlers/doc/{}".format(handler.id), "PUT", handler.json,
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply)

    @elasticRequestExceptionWrap
    @gen.coroutine
    def deleteHandler(self, handlerId):
        """
        Delete created handler by id.

        :param handlerId: the handler id
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/handlers/doc/{}".format(handlerId), "DELETE")
        return self.makeResult(reply, {
            404: lambda: {"error": Error.HandlerNotFound, "value": reply.body.decode("utf-8")}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def searchGroups(self, searchGroup: SearchGroup):
        """
        Search groups handler.

        :param searchGroup: searchGroup object
        :return: result:
            Success with a search result if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/groups/doc/_search", "POST", escape.json_encode(searchGroup.query),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            200: lambda: {"error": Error.Success, "value": prettySearch(reply)}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def addListPersonsToGroup(self, groupId, listId):
        """
        Add a Luna API person list to the group.

        :param groupId: the group id
        :param listId: a Luna API persons list
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        payload = {
            "script": {
                "source": "ctx._source['persons_lists'].add(params.listId);"
                          " ctx._source['last_update'] = params.last_update",
                "lang": "painless",
                "params": {
                    "listId": listId,
                    "last_update": getNowTimestampMillis()
                }
            }
        }

        reply = yield self.makeRequest("/groups/doc/{}/_update".format(groupId), "POST", escape.json_encode(payload),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            404: lambda: {"error": Error.GroupNotFound, "value": reply.body.decode()}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def updatePersonInGroup(self, groupId, personId):
        """
        Update person id in the group.

        :param groupId: the group id
        :param personId: person id
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        payload = {"doc": {
            'person_id': personId,
            "last_update": getNowTimestampMillis(),
        }}
        reply = yield self.makeRequest("/groups/doc/{}/_update".format(groupId), "POST", escape.json_encode(payload),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            404: lambda: {"error": Error.GroupNotFound, "value": reply.body.decode("utf-8")}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def putGroup(self, group):
        """
        Put group to es.

        :param group: a group to put
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/groups/doc/{}".format(group.id), "PUT", group.json,
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply)

    @elasticRequestExceptionWrap
    @gen.coroutine
    def getGroup(self, groupId):
        """
        Get group by id.

        :param groupId: the group id
        :return: result:
            Success with the group if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/groups/doc/{}/_source".format(groupId), "GET")
        return self.makeResult(reply, {
            404: lambda: {"error": Error.GroupNotFound, "value": reply.body.decode("utf-8")},
            200: lambda: {"error": Error.Success, "value": escape.json_decode(reply.body)}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def deleteGroup(self, groupId):
        """
        Delete created group by id.

        :param groupId: the group id
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/groups/doc/{}".format(groupId), "DELETE")
        return self.makeResult(reply, {
            404: lambda: {"error": Error.GroupNotFound, "value": reply.body.decode("utf-8")}
        })

    @elasticRequestExceptionWrap
    @lockGuard
    @gen.coroutine
    def putTask(self, task):
        """
        Put task in progress.

        :param task: task to put
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        taskIdResult = yield self.getNextTaskId()
        if taskIdResult.fail:
            return taskIdResult
        task.id = taskIdResult.value
        reply = yield self.makeRequest("/tasks/doc/{}".format(task.id), "PUT", task.json,
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply)

    @elasticRequestExceptionWrap
    @gen.coroutine
    def getNextTaskId(self):
        """
        Update the tasks counter and get the current counter value in one request.

        :return: result:
            Success with the next task id if succeed
            Fail if an error occurred
        """
        payload = {
            "script": {"source": "ctx._source.count+=1"},
            "upsert": {"count": 1},
            "fields": "_source"
        }
        reply = yield self.makeRequest("/tasks_counter/doc/0/_update?retry_on_conflict=5", "POST", escape.json_encode(payload),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            replyStatusCode: lambda: {
                "error": Error.Success,
                "value": escape.json_decode(reply.body)['get']['_source']['count']
            } for replyStatusCode in (200, 201)
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def getTask(self, taskId):
        """
        Get task by id.

        :param taskId: the task id
        :return: result:
            Success with a task if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/tasks/doc/{}/_source".format(taskId), "GET")
        return self.makeResult(reply, {
            200: lambda: {"error": Error.Success, "value": escape.json_decode(reply.body)},
            404: lambda: {"error": Error.TaskNotFound, "value": reply.body.decode("utf-8")}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def updateTaskProgress(self, taskId, progress):
        """
        Update task in progress progress value and update_time value.

        :param taskId: task to update
        :param progress: the current task progress
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        payload = {"doc": {
            'progress': progress,
            "last_update": getNowTimestampMillis(),
        }}
        reply = yield self.makeRequest("/tasks/doc/{}/_update".format(taskId), "POST", escape.json_encode(payload),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            404: lambda: {"error": Error.TaskNotFound, "value": reply.body.decode("utf-8")}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def getTaskStatus(self, taskId):
        """
        Get task in progress status by the task id.

        :param taskId: the task id
        :return: result:
            Success with task status if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/tasks/doc/{}/_source".format(taskId), "GET")
        return self.makeResult(reply, {
            200: lambda: {"error": Error.Success, "value": escape.json_decode(reply.body)['status']},
            404: lambda: {"error": Error.TaskNotFound, "value": reply.body.decode("utf-8")}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def putTaskStatus(self, taskId, status):
        """
        Put new task in progress status and update_time.

        :param taskId: the task id
        :param status: new status
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        payload = {"doc": {
            'status': status,
            "last_update": getNowTimestampMillis(),
        }}
        reply = yield self.makeRequest("/tasks/doc/{}/_update".format(taskId), "POST", escape.json_encode(payload),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply, {
            404: lambda: {"error": Error.TaskNotFound, "value": reply.body.decode("utf-8")}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def putTaskLocation(self, taskId, locationUrl):
        """
        Put location to task in progress.

        :param taskId: the task id
        :param locationUrl: location url to the finished task redirect
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        payload = {"Location": locationUrl, "id": taskId}
        reply = yield self.makeRequest("/tasks/doc/{}".format(taskId), "POST", escape.json_encode(payload),
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply)

    @elasticRequestExceptionWrap
    @lockGuard
    @gen.coroutine
    def putDoneTask(self, task):
        """
        Put done task.

        :param task: task to put
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/tasks_done/doc/{}".format(task.id), "PUT", task.json,
                                       headers={"Content-Type": "application/json"})
        return self.makeResult(reply)

    @elasticRequestExceptionWrap
    @gen.coroutine
    def getDoneTask(self, taskId):
        """
        Get done task.

        :param taskId: the done task id
        :return: result:
            Success with done task if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/tasks_done/doc/{}/_source".format(taskId), "GET")
        return self.makeResult(reply, {
            200: lambda: {"error": Error.Success, "value": escape.json_decode(reply.body)},
            404: lambda: {"error": Error.TaskNotFound, "value": reply.body.decode("utf-8")}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def deleteDoneTask(self, taskId):
        """
        Delete the done task.

        :param taskId: the done task id
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest("/tasks_done/doc/{}".format(taskId), "DELETE")
        return self.makeResult(reply, {
            200: lambda: {"error": Error.Success, "value": escape.json_decode(reply.body)},
            404: lambda: {"error": Error.TaskNotFound, "value": reply.body.decode("utf-8")}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def markTaskDone(self, task, locationUrl):
        """
        Move the task to done tasks.

        :param task: the task to move
        :param locationUrl: location to set
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        doneRes = yield self.putDoneTask(task)
        if doneRes.fail:
            return doneRes
        locationRes = yield self.putTaskLocation(task.id, locationUrl)
        return locationRes

    @elasticRequestExceptionWrap
    @gen.coroutine
    def searchTasks(self, searchTask: SearchTask):
        """
        Search tasks.

        :param searchTask: SearchTask object
        :return: result:
            Success with search response if succeed
            Fail if an error occurred
        """
        reply = yield self.makeRequest(
            "/{}/doc/_search".format('tasks_done' if searchTask.inDone else 'tasks'),
            "POST",
            escape.json_encode(searchTask.query),
            headers={"Content-Type": "application/json"}
        )
        return self.makeResult(reply, {
            200: lambda: {"error": Error.Success, "value": prettySearch(reply)}
        })

    @elasticRequestExceptionWrap
    @gen.coroutine
    def getAll(self, searchInstance, source=None):
        """
        Get up to 4M objects (events or groups) for internal purposes.

        :param searchInstance: search object
        :param source: needed fields list
        :return: result:
            Success with {'total': <total>, 'hits': <object list>} if succeed
            Fail if an error occurred
        """
        url = {
            self.SearchEvent: '/events/doc/_search',
            self.SearchGroup: '/groups/doc/_search'
        }[type(searchInstance)]
        payload = {k: v for k, v in searchInstance.query.items() if k not in ('from', )}
        payload['size'] = 10**4
        if source is not None:
            payload['_source'] = source

        totalReply = yield self.makeRequest(url + '?size=0', "POST", escape.json_encode(payload),
                                            headers={"Content-Type": "application/json"})
        totalResult = self.makeResult(totalReply, {
                200: lambda: {"error": Error.Success, "value": prettySearch(totalReply)}
            })
        if totalResult.fail:
            return totalResult

        total = totalResult.value['total']

        if total < 10**4:
            reply = yield self.makeRequest(url, "POST", escape.json_encode(payload),
                                           headers={"Content-Type": "application/json"})
            return self.makeResult(reply, {
                200: lambda: {"error": Error.Success, "value": prettySearch(reply)}
            })
        elif total < 4 * 10**5:
            max_slices = 50
        elif total < MAX_OBJECTS_TO_ATTACH:
            max_slices = total // 8000
        else:
            return Result(*{
                self.SearchEvent: (Error.TooManyEvents, total),
                self.SearchGroup: (Error.TooManyGroups, total),
            }[type(searchInstance)]
            )

        payload['slice'] = {'max': max_slices, "field": "create_time"}
        result = []
        total = 0
        for slice_num in range(max_slices):
            payload['slice']['id'] = slice_num
            reply = yield self.makeRequest(url + '?scroll=10s', "POST", escape.json_encode(payload),
                                           headers={"Content-Type": "application/json"})
            sliceRes = self.makeResult(reply)
            if sliceRes.fail:
                return sliceRes
            perttyReply = prettySearch(reply)
            result += perttyReply['hits']
            total += perttyReply['total']
        return Result(Error.Success if total == len(result) else Error.EventNotFound, {'total': len(result), 'hits': result})
