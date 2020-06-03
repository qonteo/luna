from tests.system_tests.config import ELASTICSEARCH_URL
from uuid import uuid4
import ujson as json
from requests import request


class Reply:
    json = {}
    statusCode = 0


def makeRequest(url, method, body=None, headers=None, queries=None):
    if body is not None:
        if isinstance(body, dict):
            payload = json.dumps(body, ensure_ascii=False)
            if headers is None:
                headers = {"Content-Type": "application/json"}
        else:
            payload = body
    else:
        payload = body
    reply = request(method, url, headers=headers, data=payload, params=queries)

    repText = reply.text
    if len(repText) > 0:
        repJson = json.loads(repText)
    else:
        repJson = {}
    res = Reply()
    res.json = repJson
    res.statusCode = reply.status_code
    return res

from tornado import gen
from tornado import httpclient
from tornado.httpclient import HTTPRequest
import ujson as json


@gen.coroutine
def emitEventAsync(date, handler_id, source, gender=0.5, similarity=0.5, glasses=0.5, age=0.5, tags=None, score=0.5):
    event = generateEvent(date, handler_id, source, gender, similarity, glasses, age, tags or [], score)
    eventId = event['id']
    request = HTTPRequest(url = '{}/events/doc/{}'.format(ELASTICSEARCH_URL, eventId),
                          method = "PUT",
                          headers = {"Content-Type": "application/json"},
                          body = json.dumps(event, ensure_ascii=False))
    httpClient = httpclient.AsyncHTTPClient()
    reply = yield httpClient.fetch(request)
    return reply


def emitEvent(date, handler_id, source, gender=0.5, similarity=0.5, glasses=0.5, age=0.5, tags=None, score=0.5):
    event = generateEvent(date, handler_id, source, gender, similarity, glasses, age, tags or [], score)
    eventId = event['id']
    return makeRequest('{}/events/doc/{}'.format(ELASTICSEARCH_URL, eventId), 'PUT', event)


@gen.coroutine
def emitGroupAsync(date, handler_id, source, gender=0.5, similarity=0.5, glasses=0.5, age=0.5, tags=None, score=0.5):
    group = generateGroup(date, handler_id, source, gender, similarity, glasses, age, tags or [], score)
    groupId = group['id']

    request = HTTPRequest(url = '{}/groups/doc/{}'.format(ELASTICSEARCH_URL, groupId),
                          method = "PUT",
                          headers = {"Content-Type": "application/json"},
                          body = json.dumps(group, ensure_ascii=False))
    httpClient = httpclient.AsyncHTTPClient()
    reply = yield httpClient.fetch(request)
    return reply


def emitGroup(date, handler_id, source, gender=0.5, similarity=0.5, glasses=0.5, age=0.5, tags=None, score=0.5):
    group = generateGroup(date, handler_id, source, gender, similarity, glasses, age, tags or [], score)
    groupId = group['id']
    return makeRequest('{}/groups/doc/{}'.format(ELASTICSEARCH_URL, groupId), 'PUT', group)


def generateEvent(date, handler_id, source, gender, similarity, glasses, age, tags, score):
    uuid = str(uuid4())
    return {
        "create_time": date,
        "handler_id": handler_id,
        "extract": {
            "rectISO": {
                "width": 176,
                "height": 235,
                "x": 23,
                "y": 11
            },
            "id": "91e24cff-1088-43a9-8072-31233577140d",
            "attributes": {
                "gender": gender,
                "eyeglasses": glasses,
                "age": age
            },
            "rect": {
                "width": 103,
                "height": 124,
                "x": 60,
                "y": 77
            },
            "score": score
        },
        "source": source,
        "tags": tags,
        "external_id": None,
        "id": uuid,
        "search_by_group": None,
        "group_id": "6b91894b-0cf6-484c-be15-0c651a21de47",
        "user_data": "",
        "warped_img": False,
        "error": None,
        "descriptors_lists": [],
        "person_id": None,
        "search": [
            {
                "list_id": "3e2076e6-0845-4e23-b3b5-25df12351941",
                "candidates": [
                    {
                        "similarity": 1,
                        "id": "a0785d65-bcab-4fa0-bba2-4534b5328ac9"
                    }
                ]
            },
            {
                "list_id": "c54d6393-3857-4c00-a362-4c46893341c1",
                "candidates": [
                    {
                        "similarity": similarity,
                        "person_id": "18e7e47f-0c70-4def-b173-4faaf12b02d5",
                        "user_data": "test_visionlabs_test_events_class",
                        "descriptor_id": "38480007-4571-416a-a6d9-f47831f25cb8"
                    }
                ]
            }
        ],
        "descriptor_id": uuid,
        "persons_lists": []
    }


def generateGroup(date, handler_id, source, gender, similarity, glasses, age, tags, score):
    uuid = str(uuid4())
    return {
        "id": uuid,
        "processed": True,
        "ttl": 10,
        "handler_id": handler_id,
        "create_time": date,
        "search": [
            {
                "list_id": "d015b77d-8020-4bfc-9c1c-d6164e06f94e",
                "candidate": {
                    "id": "28e5e07b-b403-4ffe-94ca-3f8b1ac8c1c5",
                    "similarity": similarity
                }
            },
            {
                "list_id": "37197ed0-29ac-4d10-8c8b-3cbef526c206",
                "candidate": {
                    "similarity": similarity,
                    "descriptor_id": "37611c4c-51f6-4db1-a8e8-0c2719b2ca42",
                    "person_id": "8ea1ad7c-d41f-486b-9ae5-cc18f8f75103",
                    "user_data": "test_visionlabs_test_groups_class"
                }
            }
        ],
        "error": None,
        "last_update": "2017-11-14T19:08:58Z",
        "attributes": {
            "age": age,
            "gender": gender
        },
        "external_tracks_id": [],
        "source": source,
        "persons_lists": [
            "e91ccdac-ef92-4d2d-b743-a99749754309"
        ],
        "person_id": "570c7cc0-dcfa-4450-ade9-700335974d49",
        "descriptors": [
            "1da1e52d-2159-42e1-a634-51ed6039ebd2"
        ]
    }
