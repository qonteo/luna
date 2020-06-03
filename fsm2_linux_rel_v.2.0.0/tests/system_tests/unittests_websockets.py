from tornado import gen, websocket, ioloop, httpclient
import ujson as json
from datetime import timedelta
from tests.system_tests.utils.group_utils import *
from uuid import uuid4

from tests.system_tests import fsmRequests, base_test_class
from tests.system_tests.config import FSM2_URL
from tests.system_tests.test_data_option import *

WS_MESSAGE_TIMEOUT = 1


class TestWebSockets(base_test_class.BaseTest):
    source = name = 'test_visionlabs_websockets'
    external_id = str(uuid4)
    group_schema = None

    @classmethod
    def setUpClass(cls):
        # create handlers
        reply = fsmRequests.createHandler({
            "name": "test_visionlabs_simple_extract_handler",
            "type": "extract",
            "multiple_faces_policy": 1
        })
        assert reply.statusCode == 201, reply.statusCode
        cls.handler_events = reply.json['handler_id']

        reply = fsmRequests.createHandler({
            "name": "test_visionlabs_simple_extract_handler_with_grouping_policy",
            "type": "extract",
            "multiple_faces_policy": 1,
            "extract_policy": {
                "estimate_attributes": 1
            },
            "grouping_policy": {
                "grouper": 1,
                "create_person_policy": {
                    "create_person": 0,
                },
                "ttl": 10,
                "threshold": 0
            },
        })
        assert reply.statusCode == 201, reply.statusCode
        cls.handler_groups = reply.json['handler_id']

        cls.loop = ioloop.IOLoop()

    def event_one_face(self):
        return fsmRequests.emitEvent(self.handler2spam, events[0], {'warped_image': 1, 'external_id': self.external_id})

    def event_four_faces(self):
        return fsmRequests.emitEvent(self.handler2spam, events[1], {'external_id': self.external_id})

    @gen.coroutine
    def checkWS(self):
        self.ws = yield websocket.websocket_connect(
            'ws' + FSM2_URL[4:] + '/api/1/ws/' + self.handler_id + '/' + self.ws_type
        )

        spamers_responses = list(map(lambda s: s(), self.spamers))
        [self.assertEqual(res.statusCode, 201, res.json) for res in spamers_responses]
        expected_result = self.prepare_spamers(spamers_responses, self.group_schema)

        result = []
        for i in range(len(expected_result) + 1):
            msg = yield self.get_ws_message()
            if msg is not None:
                result.append(json.loads(msg))
        if len(result) != len(expected_result):
            self.fail('Wrong messages count {} from expected {}\nresult {}'.format(
                len(result), len(expected_result), result
            ))

        result = self.prepare_ws(result)
        self.assertListEqual(result, expected_result, 'Got wrong ws result')

    @gen.coroutine
    def get_ws_message(self):
        try:
            msg = yield gen.with_timeout(timedelta(seconds=WS_MESSAGE_TIMEOUT), self.ws.read_message())
        except gen.TimeoutError:
            msg = None
        return msg

    def test_one_face_one_event(self):
        self.handler2spam = self.handler_id = self.handler_events
        self.spamers = [self.event_one_face]
        self.ws_type = 'events'
        self.prepare_spamers, self.prepare_ws = prepare_spamers_results_events, prepare_ws_results_events
        self.loop.run_sync(self.checkWS)

    def test_one_face_multiple_events(self):
        self.handler2spam = self.handler_id = self.handler_events
        self.spamers = [self.event_one_face] * 5
        self.ws_type = 'events'
        self.prepare_spamers, self.prepare_ws = prepare_spamers_results_events, prepare_ws_results_events
        self.loop.run_sync(self.checkWS)

    def test_multiple_faces_one_event(self):
        self.handler2spam = self.handler_id = self.handler_events
        self.spamers = [self.event_four_faces]
        self.ws_type = 'events'
        self.prepare_spamers, self.prepare_ws = prepare_spamers_results_events, prepare_ws_results_events
        self.loop.run_sync(self.checkWS)

    def test_multiple_faces_multiple_events(self):
        self.handler2spam = self.handler_id = self.handler_events
        self.spamers = [self.event_four_faces] * 5
        self.ws_type = 'events'
        self.prepare_spamers, self.prepare_ws = prepare_spamers_results_events, prepare_ws_results_events
        self.loop.run_sync(self.checkWS)

    def test_one_face_group(self):
        self.handler2spam = self.handler_id = self.handler_groups
        self.spamers = [self.event_one_face] * 5
        self.ws_type = 'events_groups'
        self.group_schema = create_group_schema([self.external_id], self.handler_id)
        self.prepare_spamers, self.prepare_ws = prepare_spamers_results_groups, prepare_ws_results_groups
        self.loop.run_sync(self.checkWS)

    def test_false_another_handler(self):
        self.handler2spam, self.handler_id = self.handler_events, self.handler_groups
        self.spamers = [self.event_one_face] * 5
        self.ws_type = 'events'
        self.prepare_spamers, self.prepare_ws = lambda *args: [], prepare_ws_results_groups
        self.loop.run_sync(self.checkWS)

    def test_wrong_handler_name(self):
        self.handler_id = 'Abudabi'
        self.ws_type = 'events'
        with self.assertRaisesRegex(httpclient.HTTPError, r'^HTTP 404: Not Found$'):
            self.loop.run_sync(self.checkWS)
