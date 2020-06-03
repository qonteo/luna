import unittest
import requests
from os import listdir
from os.path import join
import asyncio
import websockets
from re import match
from uuid import UUID
import json
from datetime import datetime, timedelta
import sys, os
from time import sleep


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
os.chdir(os.path.join(os.path.dirname(__file__)))

if sys.argv[0].find("sphinx") > 0:
    from test import config
    from test import answer
    from test import lps_events
else:
    import config
    import answer
    import lps_events


def compare(gain, expect):
    """
    Recursive function to hard-check JSON skeleton (all trees should be equal)
    and mild-check JSON values (types or re-strings).
    :param gain: json with data
    :param expect: json with re-strings or types
    :rtype: bool
    :return: True or False
    """

    def cut_ignored(elem):
        """
        The function cuts ignored fields from the element
        :param elem:
        :return:
        """
        if type(elem) not in [dict, list]:
            return
        popper = {
            list: lambda name: elem.pop(elem.index(name)) if name in elem else None,
            dict: lambda name: elem.pop if name in elem else None,
        }[type(elem)]
        [
            popper(it[0]) for it in {
                'age': config.IGNORE_AGE_TAG,
                'face_score': config.IGNORE_FACE_SCORE_TAG,
                'gender': config.IGNORE_GENDER_TAG,
                'glasses': config.IGNORE_GLASSES_TAG,
                'similarity': config.IGNORE_SIMILARITY_TAG,
            }.items() if it[1]
        ]

    def throw(gain, expect):
        e = '\nWrong format:\nGot:\n{}\nExpected type:\n{}'.format(gain, expect)
        if __debug__ is True:
            print(e)
        return False

    if isinstance(expect, dict):
        try:
            [cut_ignored(i) for i in (gain, expect)]
            res = gain.keys() == expect.keys()
            if not res:
                return throw(gain, expect)
            for k in expect:
                res *= compare(gain[k], expect[k])
            return res
        except KeyError:
            return throw(gain, expect)
        except AttributeError:
            return throw(gain, expect)
    elif isinstance(expect, list):
        try:
            [cut_ignored(i) for i in (gain, expect)]
            res = len(gain) == len(expect)
            if not res:
                return throw(gain, expect)
            for v in range(len(gain)):
                res *= compare(gain[v], expect[v])
            return res
        except IndexError:
            return throw(gain, expect)
    elif isinstance(expect, type):
        try:
            expect(gain)
            return True
        except ValueError:
            return throw(gain, expect)
        except TypeError:
            if isinstance(gain, expect):
                return True
            return throw(gain, expect)
    elif isinstance(expect, str):
        return bool(match('^' + expect + '$', gain))
    else:
        return throw(gain, expect)


class Case:
    def __init__(self, params, expect, exact, headers=None):
        """
        Test case
        :param params:
        :param expect:
        :param exact:
        :param headers:
        """
        self.params = params
        self.expect = expect
        self.exact = exact
        self.headers = headers


class RootTest(unittest.TestCase):
    # visionl@a.bs:incredible
    auth = {'Authorization': 'Basic dmlzaW9ubEBhLmJzOmluY3JlZGlibGU='}
    token = None
    list_d = None
    list_p = None
    descriptor = None
    person = None
    spamers = None

    @classmethod
    def setUpClass(cls):
        cls.create_account()
        cls.post_photos()
        cls.spamers = {
            'search': cls.search,
            'search_attributes': cls.search_attributes,
            'extract': cls.extract,
            'match': cls.match,
            'verify': cls.verify,
            'identify': cls.identify,
            'extract_attributes': cls.extract_attributes,
            'extract_token': cls.extract_token,
        }

    @classmethod
    def post_photos(cls):
        """
        The method configures Test Class:
        1) Post 5 photos, remember the last descriptor id;
        2) Attach them to the descriptor list, remember the list id;
        3) Attach them to the person, remember the person id;
        4) Attach the person to the person list, remember the list id;
        5) Get the first authorization token, remember troken id.
        :return: None
        """
        ld_reply = requests.post(config.LUNA_API_URL + 'storage/lists', params={'type': 'descriptors'},
                                 headers=cls.auth)
        assert ld_reply.status_code == 201  # Status code descriptor list create
        cls.list_d = ld_reply.json()['list_id']
        p_reply = requests.post(config.LUNA_API_URL + 'storage/persons', headers=cls.auth)
        assert p_reply.status_code == 201  # Status code person create
        cls.person = p_reply.json()['person_id']
        lp_reply = requests.post(config.LUNA_API_URL + 'storage/lists', headers=cls.auth)
        assert lp_reply.status_code == 201  # Status code person list create
        cls.list_p = lp_reply.json()['list_id']
        ptol_reply = requests.patch(config.LUNA_API_URL + 'storage/persons/{}/linked_lists'.format(cls.person),
                                    params={'list_id': cls.list_p, 'do': 'attach'}, headers=cls.auth)
        assert ptol_reply.status_code == 204  # Status code person attach to list
        url = config.LUNA_API_URL + 'storage/descriptors'
        list_url = config.LUNA_API_URL + 'storage/descriptors/{}/linked_lists'
        person_url = config.LUNA_API_URL + 'storage/persons/{}/linked_descriptors'.format(cls.person)
        for img in listdir('imgs')[:-4]:
            with open(join('imgs', img), 'rb') as _:
                reply = requests.post(url, headers={**cls.auth, 'Content-Type': 'image/jpeg'}, data=_.read())
            assert reply.status_code == 201  # Status code on descriptor create
            d_uuid = reply.json()['faces'][0]['id']
            list_reply = requests.patch(list_url.format(d_uuid), params={'do': 'attach', 'list_id': cls.list_d},
                                        headers=cls.auth)
            assert list_reply.status_code == 204  # Status code add descriptor to list
            person_reply = requests.patch(person_url, params={'do': 'attach', 'descriptor_id': d_uuid},
                                          headers=cls.auth)
            assert person_reply.status_code == 204  # Status code add descriptor to person
            cls.descriptor = d_uuid
        t_reply = requests.get(config.LUNA_API_URL + 'account/tokens', headers=cls.auth)
        assert t_reply.status_code == 200  # Get token status code
        cls.token = {'X-Auth-Token': t_reply.json()['tokens'][0]['id']}

    @classmethod
    def create_account(cls):
        account = dict(
            email='visionl@a.bs',
            password='incredible',
            organization_name='guess'
        )
        reply = requests.post(config.LUNA_API_URL + 'accounts', json=account)
        assert reply.status_code in (201, 409)  # Status code to create account

    # spamers are listed below
    @classmethod
    def search(cls):
        img = listdir('imgs')[-4]
        with open(join('imgs', img), 'rb') as _:
            reply = requests.post(config.LUNA_API_URL + 'matching/search', params={'list_id': cls.list_d},
                                  headers={**cls.auth, 'Content-type': 'image/jpeg'}, data=_.read())
            _.close()
        assert reply.status_code == 201, 'Search status code'

    @classmethod
    def search_attributes(cls):
        img = listdir('imgs')[-4]
        with open(join('imgs', img), 'rb') as _:
            reply = requests.post(config.LUNA_API_URL + 'matching/search',
                                  params={'list_id': cls.list_d, 'estimate_attributes': 1},
                                  headers={**cls.auth, 'Content-type': 'image/jpeg'}, data=_.read())
            _.close()
        assert reply.status_code == 201, 'Search with attributes status code'

    @classmethod
    def extract(cls):
        img = listdir('imgs')[-3]
        with open(join('imgs', img), 'rb') as _:
            reply = requests.post(config.LUNA_API_URL + 'storage/descriptors',
                                  headers={**cls.auth, 'Content-type': 'image/jpeg'}, data=_.read())
            _.close()
        assert reply.status_code == 201, 'Extract status code'

    @classmethod
    def extract_attributes(cls):
        images = [listdir('imgs')[-4], "SunGlasses_Claudia.jpg", "Glasses.jpg"]
        for img in images:
            with open(join('imgs', img), 'rb') as _:
                reply = requests.post(config.LUNA_API_URL + 'storage/descriptors', params={'estimate_attributes': 1},
                                      headers={**cls.auth, 'Content-type': 'image/jpeg'}, data=_.read())
                _.close()
            assert reply.status_code == 201, 'Extract with attributes status code'

    @classmethod
    def extract_token(cls):
        img = listdir('imgs')[-1]
        with open(join('imgs', img), 'rb') as _:
            reply = requests.post(config.LUNA_API_URL + 'storage/descriptors', params={'estimate_attributes': 1},
                                  headers={**cls.token, 'Content-type': 'image/jpeg'}, data=_.read())
            _.close()
        assert reply.status_code == 201, 'Extract status code'

    @classmethod
    def match(cls):
        reply = requests.post(config.LUNA_API_URL + 'matching/match',
                              params={'descriptor_id': cls.descriptor, 'list_id': cls.list_d}, headers=cls.auth)
        assert reply.status_code == 201, 'Match status code'

    @classmethod
    def verify(cls):
        reply = requests.post(config.LUNA_API_URL + 'matching/verify',
                              params={'descriptor_id': cls.descriptor, 'person_id': cls.person}, headers=cls.auth)
        assert reply.status_code == 201, 'Verify status code'

    @classmethod
    def identify(cls):
        reply = requests.post(config.LUNA_API_URL + 'matching/identify',
                              params={'descriptor_id': cls.descriptor, 'list_id': cls.list_p}, headers=cls.auth)
        assert reply.status_code == 201, 'Identify status code'


class WebSocketTest(RootTest):
    """
    Tests Event Delivery service
    """

    async def perform(self, case):
        """
        Case process:
        1) connect via websocket;
        2) send several requests to Luna API;
        3) compare data: what we received with what we expected;
        :param case: Case to work with
        :return: None
        """

        def spam(exact):
            """
            Send several requests to LUNA API
            :param exact: iter of needed events' names
            :return: None
            """
            if exact is not None:
                for elem in exact:
                    self.spamers[elem]()
            else:
                for k, v in self.spamers.items():
                    v()

        async def proceed(case):
            """
            Update authorization header if none of authorization entities are present and init a websocket
            :param case:
            :return: The first message from Statistics Service
            """
            if 'basic' not in case.params and 'auth_token' not in case.params and case.headers is None:
                case.headers = self.auth
            async with websockets.connect('ws://' + config.SS_BASE_URL + '/api/subscribe?' + \
                                                  '&'.join(('='.join((k, v)) for k, v in case.params.items())),
                                          extra_headers=case.headers  # here headers proceed in a lowercase
                                          ) as websocket:
                spam(case.exact)
                w_reply = await websocket.recv()

            return w_reply

        try:
            reply = await asyncio.wait_for(proceed(case), timeout=10)
            gain = json.loads(reply)
        except asyncio.futures.TimeoutError:
            gain = None
        if gain and 'timestamp' in gain:
            self.assertTrue(datetime.utcnow() - datetime.fromtimestamp(gain['timestamp']) < timedelta(seconds=20),
                            'Means `timestamp` in response is not in last 20 seconds (utc).')
        self.assertTrue(compare(gain, case.expect), 'Equality to expected result')

    def run_case(self, case):
        """
        The method for coroutine start
        :param case: The case to work with
        :return: None
        """
        asyncio.get_event_loop().run_until_complete(self.perform(case))

    def test_match(self):
        """
        .. test:: test_match
            
            :resources: "/api/subscribe"
            :description: receive a match event
            :tag: WS
        """
        self.run_case(Case({'event_type': 'match'}, answer.ws_match, ['extract', 'match']))
    
    def test_search_similarity_true(self):
        """
        .. test:: test_search_similarity_true
            
            :resources: "/api/subscribe"
            :description: receive a match event with the valid (high enough) similarity parameter
            :tag: WS
        """
        self.run_case(
            Case({'event_type': 'match', 'similarity__gt': '0.1'}, answer.ws_search, ['extract', 'search']))

    def test_search_similarity_false(self):
        """
        .. test:: test_search_similarity_false
            
            :resources: "/api/subscribe"
            :description: do not receive match event with invalid (too low) similarity
            :tag: WS
        """
        self.run_case(Case({'event_type': 'match', 'similarity__gt': '1'}, answer.ws_none, ['extract', 'search']))

    def test_extract_observe_basic_basic(self):
        """
        .. test:: test_extract_observe_basic_basic
            
            :resources: "/api/subscribe"
            :description: receive an extract event with basic authorization, ensure basic authorization
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'observe': 'basic'}, answer.ws_extract, ['extract']))

    def test_extract_observe_basic_token(self):
        """
        .. test:: test_extract_observe_basic_token
            
            :resources: "/api/subscribe"
            :description: do not receive an extract event with basic authorization, ensure token authorization
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'observe': 'basic'}, answer.ws_none, ['extract_token']))

    def test_extract_observe_basic_both(self):
        """
        .. test:: test_extract_observe_basic_both
            
            :resources: "/api/subscribe"
            :description: receive an extract event with basic and token authorization, ensure basic authorization
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'observe': 'basic'}, answer.ws_extract,
                           ['extract_token', 'extract']))

    def test_extract_observe_token_basic(self):
        """
        .. test:: test_extract_observe_token_basic
            
            :resources: "/api/subscribe"
            :description: do not receive an extract event with basic authorization, ensure token authorization
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'observe': self.token['X-Auth-Token']}, answer.ws_none,
                           ['extract']))

    def test_extract_observe_token_token(self):
        """
        .. test:: test_extract_observe_token_token
            
            :resources: "/api/subscribe"
            :description: receive an extract event with token authorization, ensure token authorization
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'observe': self.token['X-Auth-Token']}, answer.ws_extract_token,
                           ['extract_token']))

    def test_extract_observe_token_both(self):
        """
        .. test:: test_extract_observe_token_both
            
            :resources: "/api/subscribe"
            :description: receive an extract event with basic and token authorization, ensure token authorization
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'observe': self.token['X-Auth-Token']}, answer.ws_extract_token,
                           ['extract', 'extract_token']))

    def test_extract_observe_both_basic(self):
        """
        .. test:: test_extract_observe_both_basic
            
            :resources: "/api/subscribe"
            :description: receive an extract event with basic and token authorization, ensure both
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'observe': 'basic%2C' + self.token['X-Auth-Token']},
                           answer.ws_extract, ['extract']))

    def test_extract_observe_both_token(self):
        """
        .. test:: test_extract_observe_both_token
            
            :resources: "/api/subscribe"
            :description:  receive an extract event with token authorization, ensure both
            :tag: WS
        """
        self.run_case(
            Case({'event_type': 'extract', 'observe': 'basic%2C' + self.token['X-Auth-Token']}, answer.ws_extract_token,
                 ['extract_token']))

    def test_extract_observe_both_both_asc(self):
        """
        .. test:: test_extract_observe_both_both_asc
            
            :resources: "/api/subscribe"
            :description:  receive an extract event with basic and token authorization, ensure basic for both
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'observe': 'basic%2C' + self.token['X-Auth-Token']}, 
                           answer.ws_extract, ['extract', 'extract_token']))

    def test_extract_observe_both_both_desc(self):
        """
        .. test:: test_extract_observe_both_both_desc

            :resources: "/api/subscribe"
            :description: receive an extract event with basic and token authorization, ensure basic for both
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'observe': 'basic%2C' + self.token['X-Auth-Token']}, 
                           answer.ws_extract_token, ['extract_token', 'extract']))

    def test_extract_observe_false(self):
        """
        .. test:: test_extract_observe_false

            :resources: "/api/subscribe"
            :description: do not receive an extract event, ensure the wrong observe filter
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'observe': 'ffffffff-ffff-ffff-ffff-ffffffffffff'}, answer.ws_none,
                           ['extract', 'extract_token']))

    def test_match_list_true(self):
        """
        .. test:: test_match_list_true
            
            :resources: "/api/subscribe"
            :description: receive a match event with the right list
            :tag: WS
        """
        self.run_case(Case({'event_type': 'match', 'list': self.list_d}, answer.ws_match, ['extract', 'match']))

    def test_match_list_false(self):
        """
        .. test:: test_match_list_false
            
            :resources: "/api/subscribe"
            :description: do not receive match event with the wrong list
            :tag: WS
        """
        self.run_case(Case({'event_type': 'match', 'list': 'ffffffff-ffff-ffff-ffff-ffffffffffff'}, answer.ws_none,
                           ['extract', 'match']))

    def test_extract(self):
        """
        .. test:: test_extract
            
            :resources: "/api/subscribe"
            :description: receive an extract event
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract'}, answer.ws_extract, ['match', 'extract']))

    def test_extract_gender_true(self):
        """
        .. test:: test_extract_gender_true
            
            :resources: "/api/subscribe"
            :description: receive an extract event with correct gender filter
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'gender': 'female'}, answer.ws_extract_attributes,
                           ['match', 'extract', 'extract_attributes']))

    def test_extract_gender_false(self):
        """
        .. test:: test_extract_gender_false
            
            :resources: "/api/subscribe"
            :description: do not receive an extract event with wrong gender filter
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'gender': 'male'}, answer.ws_none,
                           ['match', 'extract', 'extract_attributes']))

    def test_extract_age_true(self):
        """
        .. test:: test_extract_age_true
            
            :resources: "/api/subscribe"
            :description: receive an extract event with correct age filter
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'age__gt': '0', 'age__lt': '9999'}, answer.ws_extract_attributes,
                           ['match', 'extract', 'extract_attributes']))

    def test_extract_age_false(self):
        """
        .. test:: test_extract_age_false
            
            :resources: "/api/subscribe"
            :description: do not receive an extract event with wrong age filter
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'age__gt': '9999', 'age__lt': '0'}, answer.ws_none,
                           ['match', 'extract', 'extract_attributes']))

    def test_extract_glasses_true(self):
        """
        .. test:: test_extract_glasses_true
            
            :resources: "/api/subscribe"
            :description: receive an extract event with correct glasses filter
            :tag: WS
        """
        self.run_case(
            Case({'event_type': 'extract', 'glasses__gt': '0', 'glasses__lt': '1'}, answer.ws_extract_attributes,
                 ['match', 'extract', 'extract_attributes']))

    def test_extract_glasses_false(self):
        """
        .. test:: test_extract_glasses_false
            
            :resources: "/api/subscribe"
            :description: do not receive an extract event with wrong glasses filter
            :tag: WS
        """
        self.run_case(Case({'event_type': 'extract', 'glasses__gt': '1', 'glasses__lt': '0'}, answer.ws_none,
                           ['match', 'extract', 'extract_attributes']))

    def test_auth_token_query(self):
        """
        .. test:: test_auth_token_query

            :resources: "/api/subscribe"
            :description: subscribe via authorization token parameter
            :tag: WS
        """
        self.run_case(Case({'auth_token': self.token['X-Auth-Token']}, answer.ws_search, ['search']))

    def test_auth_token_header(self):
        """
        .. test:: test_auth_token_header
        
            :resources: "/api/subscribe"
            :description: subscribe via authorization token header
            :tag: WS
        """
        self.run_case(Case({}, answer.ws_search, ['search'], self.token))

    def test_auth_basic_query(self):
        """
        .. test:: test_auth_basic_query
        
            :resources: "/api/subscribe"
            :description: subscribe with basic authorization parameter
            :tag: WS
        """
        self.run_case(Case({'basic': self.auth['Authorization'].replace(' ', '%20')}, answer.ws_search, ['search']))

    def test_auth_basic_header(self):
        """
        .. test:: test_auth_basic_header
        
            :resources: "/api/subscribe"
            :description: subscribe with basic authorization header
            :tag: WS
        """
        self.run_case(Case({}, answer.ws_search, ['search'], self.auth))


class HTTPTest(RootTest):
    """
    Tests Statistic service
    """

    url = 'http://' + config.SS_BASE_URL + '/api/events'

    @classmethod
    def warm_influx_up(cls):
        for k in ['extract_attributes', 'search_attributes']:
            cls.spamers[k]()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warm_influx_up()

    def proceed(self, case, status_code=200, is_json=True):
        sleep(3)  # for test autonomy
        self.time = datetime.utcnow()
        if case.exact is None:
            for k, v in self.spamers.items():
                v()
        else:
            for k in case.exact:
                self.spamers[k]()
        sleep(1)
        if 'basic' not in case.params and 'auth_token' not in case.params and case.headers is None:
            case.headers = self.auth
        if 'time__gt' not in case.params:
            delta = round((datetime.utcnow() - self.time).total_seconds()) + 2
            case.params.update({'time__gt': 'now-' + str(delta) + 's'})
        reply = requests.get(self.url, params=case.params, headers=case.headers)
        self.assertEqual(reply.status_code, status_code, 'Status code get statistic\nBody:' + reply.text)
        if is_json:
            self.assertTrue(compare(reply.json(), case.expect), 'Cannot compare reply json:\n' + reply.text)
        else:
            self.assertTrue(compare(reply.text, case.expect), 'Cannot compare reply text:\n' + reply.text)
        if case.expect == answer.http_extract_attributes:
            if "glasses__lt" in case.params:
                self.assertEqual(reply.json()['values'][0][-1], 0, reply.json())
            elif "glasses__gt" in case.params:
                self.assertEqual(reply.json()['values'][0][-1], 1, reply.json())

    def test_extract(self):
        """
        .. test:: test_extract
            
            :resources: "/api/events"
            :description: get statistics on an extract event
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract'}, answer.http_extract, ['extract']))

    def test_match(self):
        """
        .. test:: test_match
            
            :resources: "/api/events"
            :description: get statistics on match events
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match'}, answer.http_match, ['match']))

    def test_source_true(self):
        """
        .. test:: test_source_true

            :resources: "/api/events"
            :description: get statistics on match events with the right source
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'source': 'match'}, answer.http_match, ['match']))

    def test_source_false(self):
        """
        .. test:: test_source_false

            :resources: "/api/events"
            :description: do not get statistics on match events with the wrong source
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'source': 'search'}, answer.http_none, ['match']))

    def test_match_aggregator_count(self):
        """
        .. test:: test_match_aggregator_count
            
            :resources: "/api/events"
            :description: get statistics on match events with count aggregator
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'aggregator': 'count'}, answer.http_match, ['match', 'match']))

    def test_match_aggregator_min(self):
        """
        .. test:: test_match_aggregator_min
            
            :resources: "/api/events"
            :description: get statistics on match events with min aggregator
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'aggregator': 'min'}, answer.http_match, ['match']))

    def test_match_aggregator_max(self):
        """
        .. test:: test_match_aggregator_max
            
            :resources: "/api/events"
            :description: get statistics on match events with max aggregator
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'aggregator': 'max'}, answer.http_match, ['match']))

    def test_match_aggregator_mean(self):
        """
        .. test:: test_match_aggregator_mean
            
            :resources: "/api/events"
            :description: get statistics on match events with mean aggregator
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'aggregator': 'mean'}, answer.http_match, ['match', 'match']))

    def test_match_time_true(self):
        """
        .. test:: test_match_time_true
            
            :resources: "/api/events"
            :description: get statistics on match events with the correct time filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'time__gt': 'now-9999w', 'group_step': '9999w'}, answer.http_any_one,
                          ['match', 'match']))

    def test_match_time_false(self):
        """
        .. test:: test_match_time_false
            
            :resources: "/api/events"
            :description: do not get statistics on match events with zero-length time filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'time__gt': 'now'}, answer.http_none, ['match']))

    def test_match_absolute_time_true(self):
        """
        .. test:: test_match_absolute_time_true

            :resources: "/api/events"
            :description: get statistics on match events with correct absolute time in the different format
            :tag: HTTP
        """
        sleep(1)  # for test autonomy
        self.proceed(Case({'event_type': 'match', 'time__gt': datetime.now().strftime('%Y-%m-%d-%H-%M-%S')},
                          answer.http_match, ['match']))
        self.proceed(Case({'event_type': 'match', 'time__gt': (datetime.now()).strftime('%Y-%m-%d-%H-%M')},
                          answer.http_any_one, ['match']))
        self.proceed(Case({'event_type': 'match', 'time__gt': (datetime.now()).strftime('%Y-%m-%d-%H')},
                          answer.http_any_one, ['match']))
        self.proceed(Case({'event_type': 'match', 'time__gt': (datetime.utcnow()).strftime('%Y-%m-%d'),
                           'group_step': '2d', 'aggregator': 'count'}, answer.http_any_one, ['match']))
        self.proceed(Case({'event_type': 'match', 'time__gt': (datetime.now()).strftime('%Y-%m'),
                           'group_step': '5w'}, answer.http_any_one, ['match']))
        self.proceed(Case({'event_type': 'match', 'time__gt': (datetime.now()).strftime('%Y'),
                           'group_step': '53w'}, answer.http_any_one, ['match']))

    def test_match_absolute_time_false(self):
        """
        .. test:: test_match_absolute_time_false

            :resources: "/api/events"
            :description: do not get statistics on match events with zero-length absolute time filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match',
                           'time__gt': datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
                           'time__lt': datetime.now().strftime('%Y-%m-%d-%H-%M-%S')},
                          answer.http_none, ['match']))

    def test_match_absolute_time_future(self):
        """
        .. test:: test_match_absolute_time_future

            :resources: "/api/events"
            :description: do not get statistics on match events with absolute time filter in future
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match',
                           'time__gt': (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d-%H-%M-%S')},
                          answer.http_none, []))
        self.proceed(Case({'event_type': 'match',
                           'time__gt': (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d-%H-%M-%S')},
                          answer.http_none, []))

    def test_match_time_edges(self):
        """
        .. test:: test_match_time_edges

            :resources: "/api/events"
            :description: check "time" edges on match events in future and far past
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'time__gt': 'now-9999999w'},
                          answer.http_group_step_too_big, []), 400, False)
        self.proceed(Case({'event_type': 'match', 'time__gt': 'now+9999999w', 'time__lt': 'now+10000000w'},
                          answer.http_time_wrong_value, []), 400, False)

    def test_match_absolute_time_edges(self):
        """
        .. test:: test_match_absolute_time_edges

            :resources: "/api/events"
            :description: check absolute "time" edges on match events in future, in far past, on nonexistent day
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'time__gt': '1969-01-01'},
                          answer.http_time_gt_negative_timestamp, []), 400, False)
        self.proceed(Case({'event_type': 'match', 'time__gt': '9998'},
                          answer.http_error_parsing_query, []), 400, False)
        self.proceed(Case({'event_type': 'match', 'time__gt': '2017-02-30'},
                          answer.http_time_gt_wrong_value, []), 400, False)

    def test_match_group_step_edges(self):
        """
        .. test:: test_match_group_step_edges

            :resources: "/api/events"
            :description: check "group_step" edges if negative, zero or too large
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'group_step': '0s'},
                          answer.http_group_step_too_small, []), 400, False)
        self.proceed(Case({'event_type': 'match', 'group_step': '9999999w'},
                          answer.http_group_step_too_big, []), 400, False)
        self.proceed(Case({'event_type': 'match', 'group_step': '-1h'},
                          answer.http_group_step_wrong_value, []), 400, False)

    def test_match_observe_true(self):
        """
        .. test:: test_match_observe_true
            
            :resources: "/api/events"
            :description: get statistics on match events with correct observe filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'observe': 'basic'}, answer.http_match, ['match']))

    def test_match_observe_false(self):
        """
        .. test:: test_match_observe_false
            
            :resources: "/api/events"
            :description: do not get statistics on match events with wrong observe filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'observe': 'ffffffff-ffff-ffff-ffff-ffffffffffff'}, answer.http_none,
                          ['match']))

    def test_match_auth_token_query(self):
        """
        .. test:: test_match_auth_token_query
            
            :resources: "/api/events"
            :description: get statistics on match events with token in query
            :tag: HTTP
        """
        self.proceed(
            Case({'event_type': 'match', 'auth_token': self.token['X-Auth-Token']}, answer.http_match, ['match']))

    def test_match_auth_token_header(self):
        """
        .. test:: test_match_auth_token_header
            
            :resources: "/api/events"
            :description: get statistics on match events with token in header
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match'}, answer.http_match, ['match'], self.token))

    def test_match_auth_basic_query(self):
        """
        .. test:: test_match_auth_basic_query
            
            :resources: "/api/events"
            :description: get statistics on match events with basic authorization in query
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'basic': self.auth['Authorization']}, answer.http_match, ['match']))

    def test_match_auth_basic_header(self):
        """
        .. test:: test_match_auth_basic_header
            
            :resources: "/api/events"
            :description: get statistics on match events with  basic authorization in header
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match'}, answer.http_match, ['match'], self.auth))

    def test_match_similarity_true(self):
        """
        .. test:: test_match_similarity_true
            
            :resources: "/api/events"
            :description: get statistics on match events with valid similarity filter
            :tag: HTTP
        """
        self.proceed(
            Case({'event_type': 'match', 'similarity__gt': '0.9', 'similarity__lt': '1.1'}, answer.http_match,
                 ['match']))

    def test_match_similarity_lt_false(self):
        """
        .. test:: test_match_similarity_lt_false

            :resources: "/api/events"
            :description: do not get statistics on match events with invalid similarity filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'similarity__lt': '0'}, answer.http_none, ['match']))

    def test_match_similarity_gt_false(self):
        """
        .. test:: test_match_similarity_gt_false

            :resources: "/api/events"
            :description: do not get statistics on match events with invalid similarity filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'similarity__gt': '1'}, answer.http_none, ['match']))

    def test_match_list_false(self):
        """
        .. test:: test_match_list_false
            
            :resources: "/api/events"
            :description: do not get statistics on match events with invalid list filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'list': 'ffffffff-ffff-ffff-ffff-ffffffffffff'}, answer.http_none,
                          ['match']))

    def test_match_list_true(self):
        """
        .. test:: test_match_list_true
            
            :resources: "/api/events"
            :description: get statistics on match events with valid list filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'list': self.list_d}, answer.http_match, ['match']))

    def test_extract_source_true(self):
        """
        .. test:: test_extract_source_true
            
            :resources: "/api/events"
            :description: get statistics on extract events with valid source filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract', 'source': 'descriptors'}, answer.http_extract, ['extract']))

    def test_extract_source_false(self):
        """
        .. test:: test_extract_source_false
            
            :resources: "/api/events"
            :description: do not get statistics on extract events with match source filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract', 'source': 'match'}, answer.http_none, ['extract']))

    def test_match_source_true(self):
        """
        .. test:: test_match_source_true
            
            :resources: "/api/events"
            :description: get statistics on match events with valid source filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'source': 'match'}, answer.http_match, ['match']))

    def test_match_source_false(self):
        """
        .. test:: test_match_source_false
            
            :resources: "/api/events"
            :description: do not get statistics on match events with extractor source filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'source': 'extract'}, answer.http_none, ['extract']))

    def test_identify_source_true(self):
        """
        .. test:: test_identify_source_true
            
            :resources: "/api/events"
            :description: get statistics on identify events with valid source filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'source': 'identify'}, answer.http_identify, ['identify']))

    def test_verify_source_true(self):
        """
        .. test:: test_verify_source_true
            
            :resources: "/api/events"
            :description: get statistics on verify events with valid source filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'source': 'verify'}, answer.http_verify, ['verify']))

    def test_search_source_true(self):
        """
        .. test:: test_search_source_true
            
            :resources: "/api/events"
            :description: get statistics on search events with valid source filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'match', 'source': 'search'}, answer.http_search, ['search']))

    def test_extract_face_score_true(self):
        """
        .. test:: test_extract_face_score_true
            
            :resources: "/api/events"
            :description: get statistics on extract events with valid face_score filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract', 'face_score__gt': '0'}, answer.http_extract, ['extract']))

    def test_extract_face_score_false(self):
        """
        .. test:: test_extract_face_score_false
            
            :resources: "/api/events"
            :description: do not get statistics on extract events with invalid face_score filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract', 'face_score__gt': '1'}, answer.http_none, ['extract_attributes']))

    def test_extract_gender_true(self):
        """
        .. test:: test_extract_gender_true
            
            :resources: "/api/events"
            :description: get statistics on extract events with valid gender filter
            :tag: HTTP
        """
        self.proceed(
            Case({'event_type': 'extract', 'gender': 'female'}, answer.http_extract_attributes, ['extract_attributes']))

    def test_extract_gender_false(self):
        """
        .. test:: test_extract_gender_false
            
            :resources: "/api/events"
            :description: do not get statistics on extract events with invalid gender filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract', 'gender': 'male'}, answer.http_none, ['extract_attributes']))

    def test_extract_over_exposed_lt_false(self):
        """
        .. test:: test_extract_over_exposed_false

            :resources: "/api/events"
            :description: do not get statistics on extract events with invalid over_exposed filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract', 'over_exposed__lt': '0'}, answer.http_none,
                          ['extract_attributes']))

    def test_extract_glasses_true(self):
        """
        .. test:: test_extract_glasses_true
            
            :resources: "/api/events"
            :description: get statistics on extract events with valid glasses filter
            :tag: HTTP
        """
        cases = {"glasses__lt": "No glasses", "glasses__gt": "With glasses"}
        for case in cases:
            with self.subTest(case=cases[case]):
                self.proceed(
                    Case({'event_type': 'extract', case: 0.5}, answer.http_extract_attributes,
                         ['extract_attributes']))

    def test_extract_glasses_gt_false(self):
        """
        .. test:: test_extract_glasses_false
            
            :resources: "/api/events"
            :description: do not get statistics on extract events with invalid glasses filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract', 'glasses__gt': '1'}, answer.http_none,
                          ['extract_attributes']))

    def test_extract_glasses_lt_false(self):
        """
        .. test:: test_extract_glasses_false

            :resources: "/api/events"
            :description: do not get statistics on extract events with invalid glasses filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract', 'glasses__lt': '0'}, answer.http_none,
                          ['extract_attributes']))

    def test_extract_age_true(self):
        """
        .. test:: test_extract_age_true
            
            :resources: "/api/events"
            :description: get statistics on extract events with valid age filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract', 'age__gt': '0', 'age__lt': '9999'}, answer.http_extract_attributes,
                          ['extract_attributes']))

    def test_extract_age_gt_false(self):
        """
        .. test:: test_extract_age_false
            
            :resources: "/api/events"
            :description: do not get statistics on extract events with invalid age filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract', 'age__gt': '9999'}, answer.http_none,
                          ['extract_attributes']))

    def test_extract_age_lt_false(self):
        """
        .. test:: test_extract_age_false

            :resources: "/api/events"
            :description: do not get statistics on extract events with invalid age filter
            :tag: HTTP
        """
        self.proceed(Case({'event_type': 'extract', 'age__lt': '0'}, answer.http_none,
                          ['extract_attributes']))


class CookieTest(RootTest):
    """
    Tests Login service
    """

    url = 'http://' + config.SS_BASE_URL + '/login'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        reply = requests.post(url=cls.url, headers=cls.auth)
        assert reply.status_code == 201, 'Get cookie status_code'
        cls.cookies = {'Authorization': reply.cookies['Authorization']}

    def test_status(self):
        """
        .. test:: test_status

            :resources: "/login"
            :description: correct cookie status 
            :tag: HTTP
        """
        reply = requests.get(self.url, cookies=self.cookies)
        self.assertEqual(reply.status_code, 200, 'Cannot assert status_code, body:\n' + reply.text)

    def test_none_status(self):
        """
        .. test:: test_none_status

            :resources: "/login"
            :description: invalid cookie status 
            :tag: HTTP
        """
        reply = requests.get(self.url)
        self.assertEqual(reply.status_code, 401, 'Cannot assert status_code, body:\n' + reply.text)
        self.assertEqual(reply.text, 'Cookie not found', 'Cannot assert content')

    def test_wrong_status(self):
        """
        .. test:: test_wrong_status

            :resources: "/login"
            :description: get corrupted cookie status
            :tag: HTTP
        """
        cookies = {'Authorization': self.cookies['Authorization'][:-1]}
        reply = requests.get(self.url, cookies=cookies)
        self.assertEqual(reply.status_code, 401, 'Cannot assert status_code, body:\n' + reply.text)
        self.assertEqual(reply.text, 'Cookie not found', 'Cannot assert content')

    def test_delete(self):
        """
        .. test:: test_delete

            :resources: "/login"
            :description: delete cookie test
            :tag: HTTP
        """
        reply = requests.delete(self.url, cookies=self.cookies)
        self.assertEqual(reply.status_code, 204, 'Cannot assert status_code, body:\n' + reply.text)
        self.assertNotIn('Authorization', reply.cookies)

    def test_match(self):
        """
        .. test:: test_match

            :resources: "/api/events"
            :description: match with cookie authorization
            :tag: HTTP
        """
        time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        sleep(1)  # for test autonomy
        self.spamers['match']()
        reply = requests.get('http://{}/api/events'.format(config.SS_BASE_URL), params={
            'time__gt': time,
            'event_type': 'match'
        }, cookies=self.cookies)

        self.assertEqual(reply.status_code, 200, 'Cannot assert status_code, body:\n' + reply.text)
        self.assertNotEqual(reply.text, '{}', 'Cannot assert content')

    def test_post_method_false(self):
        """
        .. test:: test_post_method_false

            :resources: "/api/events"
            :description: post empty request
            :tag: HTTP
        """
        reply = requests.post(self.url)
        self.assertEqual(reply.status_code, 400, 'Cannot assert status_code, body:\n' + reply.text)
        self.assertEqual(reply.text, 'No credentials provided', 'Cannot assert content')


class InternalEventTest(unittest.TestCase):
    """
    Tests Luna Event service
    """
    maxDiff = None

    url = config.LPSE_URL

    def test_post_event(self):
        """
        .. test:: test_post_event

            :resources: "/internal/lps_event"
            :description: post normal LUNA API event 
            :tag: HTTP
        """
        reply1 = requests.post(self.url, json=lps_events.extract_event)
        reply2 = requests.post(self.url, json=lps_events.descriptor_event)
        reply3 = requests.post(self.url, json=lps_events.match_no_candidates_event)
        self.assertEqual(reply1.status_code, 201, 'Cannot assert status_code, body:\n' + reply1.text)
        self.assertEqual(reply2.status_code, 201, 'Cannot assert status_code, body:\n' + reply2.text)
        self.assertEqual(reply3.status_code, 201, 'Cannot assert status_code, body:\n' + reply3.text)
        self.assertEqual(reply1.text, '', 'Cannot assert body')
        self.assertEqual(reply2.text, '', 'Cannot assert body')
        self.assertEqual(reply3.text, '', 'Cannot assert body')

    def test_post_no_json(self):
        """
        .. test:: test_post_no_json

            :resources: "/internal/lps_event"
            :description: post no data
            :tag: HTTP
        """
        reply = requests.post(self.url)
        self.assertEqual(reply.status_code, 400, 'Cannot assert status_code, body:\n' + reply.text)
        self.assertEqual(reply.text, '1001: Cannot parse json ', 'Cannot assert body')

    def test_post_corrupt_json(self):
        """
        .. test:: test_post_corrupt_json

            :resources: "/internal/lps_event"
            :description: post corrupt LUNA API event
            :tag: HTTP
        """
        reply = requests.post(self.url, data=json.dumps(lps_events.extract_event)[:-1])
        self.assertEqual(reply.status_code, 400, 'Cannot assert status_code, body:\n' + reply.text)
        self.assertEqual(reply.text, '1001: Cannot parse json b\'' + json.dumps(lps_events.extract_event)[:-1] + '\'',
                         'Cannot assert body')

    def test_post_wrong_schema_json(self):
        """
        .. test:: test_post_wrong_schema_json

            :resources: "/internal/lps_event"
            :description: post invalid LUNA API event
            :tag: HTTP
        """
        reply = requests.post(self.url, json={})
        self.assertEqual(reply.status_code, 400, 'Cannot assert status_code, body:\n' + reply.text)
        self.assertEqual(reply.text, '', 'Cannot assert body')

    def test_post_incomplete_json(self):
        """
        .. test:: test_post_incomplete_json

            :resources: "/internal/lps_event"
            :description: post incomplete LUNA API event
            :tag: HTTP
        """
        reply = requests.post(self.url, json={"event_type": "c8addfa1-626a-47d1-8c63-bd8bb8ff8138"})
        self.assertEqual(reply.status_code, 400, 'Cannot assert status_code, body:\n' + reply.text)
        self.assertEqual(reply.text, '1001: Cannot parse json - wrong "event_type"', 'Cannot assert body')

    def test_post_bad_authorization_json(self):
        """
        .. test:: test_post_corrupt_json

            :resources: "/internal/lps_event"
            :description: post LUNA API event with invalid authorization data
            :tag: HTTP
        """
        js = {**lps_events.extract_event, 'authorization': float('inf')}
        reply = requests.post(self.url, json=js)
        self.assertEqual(reply.status_code, 400, 'Cannot assert status_code, body:\n' + reply.text)
        self.assertEqual(reply.text, '1001: Cannot parse json b\'' + json.dumps(js) + '\'', 'Cannot assert body')

    def test_other_methods(self):
        """
        .. test:: test_other_methods

            :resources: "/internal/lps_event"
            :description: send requests with different methods
            :tag: HTTP
        """
        methods = [
            'GET', 'PUT', 'PATCH', 'DELETE', 'HEAD',
            'COPY', 'OPTIONS', 'LINK', 'UNLINK', 'PURGE', 'LOCK', 'UNLOCK', 'PROPFIND'
        ]
        replies = [requests.request(m, self.url) for m in methods]
        [self.assertEqual(reply.status_code, 405, 'Assert status code') for reply in replies]
