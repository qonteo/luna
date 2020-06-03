import copy

from lunavl.httpclient import LunaHttpClient
import requests
from unittest import TestCase, skip

from tests.system_tests import fsmRequests
from tests.system_tests.config import LUNA_API_HOST, LUNA_AUTH_TOKEN, LUNA_API_API, LUNA_API_PORT, \
    ELASTICSEARCH_URL as ES_URL, FSM2_URL, FSM2_API_VERSION
from itertools import chain
from time import sleep

MAX_RETRIES = 3


def retry(func, status_code, *args, **kwargs):
    for i in range(MAX_RETRIES):
        reply = func(*args, **kwargs)
        if reply.status_code != status_code:
            return reply
        print('Retrying {}({},{})'.format(func, args, kwargs))
        sleep(5)


def skipWithIncrementCount(reason):
    BaseTest.runningTestsCount -= 1
    return skip(reason)


class BaseTest(TestCase):
    listsToDelete = []
    personsToDelete = []
    tasksToDelete = []
    lunaClient = LunaHttpClient(endPoint=LUNA_API_HOST, token=LUNA_AUTH_TOKEN, port=LUNA_API_PORT, api=LUNA_API_API)

    runningTestsCount = 0

    def __init__(self, *args, **kwargs):
        super(BaseTest, self).__init__(*args, **kwargs)
        BaseTest.runningTestsCount += 1

    @staticmethod
    def getHandlerIds():
        query = {"stored_fields": ["_id"], "query": {"match_phrase_prefix": {"name": "test_visionlabs_"}}}
        reply = requests.post(ES_URL + '/handlers/doc/_search?size=10000', json=query)
        assert reply.status_code == 200, "Wrong status code, body:" + reply.text
        return [h['_id'] for h in reply.json()['hits']['hits']]

    @staticmethod
    def cleanUpElastic(handlerIds):
        handlerQuery = {"query": {"match_phrase_prefix": {"name": "test_visionlabs_"}}}
        otherQuery = {"query": {"bool": {"should": [
            {"match": {"handler_id": handlerId}} for handlerId in handlerIds
        ]}}}
        res1 = retry(requests.post, 409, ES_URL + "/handlers/doc/_delete_by_query", json=handlerQuery)
        assert res1.status_code == 200, '{}: {}'.format(res1.status_code, res1.text)
        res2 = retry(requests.post, 409, ES_URL + "/groups/doc/_delete_by_query", json=otherQuery)
        assert res1.status_code == 200, '{}: {}'.format(res1.status_code, res2.text)
        res3 = retry(requests.post, 409, ES_URL + "/events/doc/_delete_by_query", json=otherQuery)
        assert res1.status_code == 200, '{}: {}'.format(res1.status_code, res3.text)

    @staticmethod
    def getTaskIds():
        payload = {
            "size": 10000,
            "_source": "id",
            "query": {"match_phrase_prefix": {"task.description": "test_visionlabs_"}}
        }
        reply = retry(requests.post, 409, ES_URL + "/tasks_done/doc/_search", json=payload)
        taskIds = [hit["_source"]["id"] for hit in reply.json()['hits']['hits']]
        return taskIds

    @staticmethod
    def deleteTasks(taskIds):
        payload = {"query": {"bool": {"should": [
            {"match": {"id": taskId}} for taskId in taskIds
        ]}}}
        reply = retry(requests.post, 409, ES_URL + "/tasks/doc/_delete_by_query", json=payload)
        assert reply.status_code == 200, "{}: {}".format(reply.status_code, reply.text)
        reply = retry(requests.post, 409, ES_URL + "/tasks_done/_delete_by_query", json=payload)
        assert reply.status_code == 200, "{}: {}".format(reply.status_code, reply.text)

    @staticmethod
    def deleteReports(taskIds):
        from multiprocessing.dummy import Pool
        threadMap = Pool(50).map
        addresses = ['{}/api/{}/reports/{}'.format(FSM2_URL, FSM2_API_VERSION, taskId) for taskId in taskIds]
        replies = threadMap(requests.delete, addresses)
        assert all(reply.status_code in (204, 404) for reply in replies), \
            '\n'.join(
                "{}: {}".format(reply.status_code, reply.text)
                for reply in replies
                if reply.status_code not in (204, 404)
            )

    @staticmethod
    def getTargetFromJsonByName(js, target: str):
        if isinstance(js, dict):
            if target in js and js[target] is not None:
                yield js[target]
            for v in js.values():
                yield from BaseTest.getTargetFromJsonByName(v, target)
        elif isinstance(js, list):
            for v in js:
                yield from BaseTest.getTargetFromJsonByName(v, target)

    @staticmethod
    def getLists(handlerIds, taskIds):
        handlerQuery = {"query": {"bool": {"should": [
            {"match": {"_id": handlerId}} for handlerId in handlerIds
        ]}}}
        reply = requests.post(ES_URL + '/handlers/doc/_search?size=10000', json=handlerQuery)
        assert reply.status_code == 200, "Wrong ES reply status code"
        js_handlers = reply.json()

        taskQuery = {"query": {"bool": {"should": [
            {"match": {"id": taskId}} for taskId in taskIds
        ]}}}
        reply = requests.post(ES_URL + '/tasks_done/doc/_search?size=10000', json=taskQuery)
        assert reply.status_code == 200, "Wrong ES reply status code"
        js_tasks = reply.json()
        return set(BaseTest.getTargetFromJsonByName([js_handlers, js_tasks], 'list_id'))

    @staticmethod
    def getPersons(handlerIds):
        eventQuery = {"query": {"bool": {"should": [
            {"match": {"handler_id": handlerId}} for handlerId in handlerIds
        ]}}}
        events_reply = requests.post(ES_URL + '/events/doc/_search?size=10000', json=eventQuery)
        groups_reply = requests.post(ES_URL + '/groups/doc/_search?size=10000', json=eventQuery)
        assert events_reply.status_code == 200, "Wrong ES reply status code"
        assert groups_reply.status_code == 200, "Wrong ES reply status code"
        js = [events_reply.json(), groups_reply.json()]
        return set(BaseTest.getTargetFromJsonByName(js, 'person_id'))

    @staticmethod
    def deleteLunaAPILists(lists):
        for list_ in lists:
            reply = BaseTest.lunaClient.deleteList(list_)
            assert reply.statusCode == 204 or reply.statusCode == 404, "Delete list failure, body:{}".format(reply.request.body)

    @staticmethod
    def deleteLunaAPIPersons(persons):
        for p in persons:
            del_reply = BaseTest.lunaClient.deletePerson(p)
            assert del_reply.statusCode in [204, 404], "Delete list failure, body:{}".format(del_reply.request.body)

    def tearDown(self):
        BaseTest.runningTestsCount -= 1

    @classmethod
    def tearDownClass(cls):
        if BaseTest.runningTestsCount == 0:
            sleep(20)
            taskIds = set(chain(cls.tasksToDelete, cls.getTaskIds()))
            handlers = cls.getHandlerIds()
            lists = cls.getLists(handlers, taskIds)
            persons = cls.getPersons(handlers)
            cls.deleteLunaAPIPersons(chain(persons, cls.personsToDelete))
            cls.deleteLunaAPILists(set(chain(lists, cls.listsToDelete)))
            cls.cleanUpElastic(handlers)
            cls.deleteReports(taskIds)
            cls.deleteTasks(taskIds)

    def corrupt_test(self, perfect_task, paths, task_create_func):
        corruption = {"some_nonexistent_field": "fail"}
        for path in paths:
            with self.subTest("Corrupt json in '{}'".format(path)):
                dict2change = corrupt_task = copy.deepcopy(perfect_task)
                if path:
                    for p in path.split('.'):
                        if p.isdigit():
                            p = int(p)
                        dict2change = dict2change[p]

                if not isinstance(dict2change, dict):
                    self.fail("Wrong path '{}' provided".format(path))
                dict2change.update(corruption)

                reply = task_create_func(corrupt_task)
                self.assertEqual(reply.statusCode, 400)
                self.assertEqual(12019, reply.json["error_code"])
                self.assertTrue(
                    (
                        "Failed to validate input json. "
                        "Path: '{}',  "
                        "message: 'Additional properties are not allowed ('some_nonexistent_field' was unexpected)'"
                    ).format(path) ==
                    reply.json["detail"]
                    or
                    next(iter(corruption)) in reply.json["detail"] and
                    reply.json['detail'].endswith(" is not valid under any of the given schemas'"), reply.json
                )

    @staticmethod
    def wait_tasks_ready(task_ids):
        task_ids = list(task_ids)
        sleep(0.2 * len(task_ids))
        for task_id in task_ids:
            for i in range(600):
                reply = fsmRequests.getTaskInProgress(task_id)
                if reply.statusCode == 303:
                    break
                assert reply.statusCode == 200, reply.json
                sleep(0.1)
            else:
                raise RuntimeError("Task '{}' is not done".format(task_id))
