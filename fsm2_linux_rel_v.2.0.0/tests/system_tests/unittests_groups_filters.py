from itertools import chain
from time import sleep
from datetime import datetime
from uuid import uuid4
from tests.system_tests import fsmRequests, base_test_class, handlers_examples
from tests.system_tests.test_data_option import *


class TestGroups(base_test_class.BaseTest):
    name = 'test_visionlabs_test_groups_class'
    start = None
    stop = None
    events = {}

    @classmethod
    def setUpClass(cls):
        # create lists
        reply = cls.lunaClient.createList('descriptors', cls.name)
        assert reply.statusCode == 201, reply.statusCode
        inputListDescriptors = reply.body['list_id']

        reply = cls.lunaClient.createList('persons', cls.name)
        assert reply.statusCode == 201, reply.statusCode
        inputListPersons = reply.body['list_id']

        reply = cls.lunaClient.createList('persons', cls.name)
        assert reply.statusCode == 201, reply.statusCode
        outputList = reply.body['list_id']

        # create descriptors
        for d in descriptorsImgs_search:
            reply = cls.lunaClient.extractDescriptors(filename=d)
            assert reply.statusCode == 201, reply.statusCode
            dId = reply.body["faces"][0]["id"]

            reply = cls.lunaClient.linkListToDescriptor(dId, inputListDescriptors)
            assert reply.statusCode == 204, reply.statusCode

        # create persons
        for p in personsImgs_search:
            reply = cls.lunaClient.createPerson(cls.name)
            assert reply.statusCode == 201, reply.statusCode
            pId = reply.body['person_id']
            cls.personsToDelete += [pId]

            reply = cls.lunaClient.extractDescriptors(filename=p)
            assert reply.statusCode == 201, reply.statusCode
            dId = reply.body["faces"][0]["id"]

            reply = cls.lunaClient.linkDescriptorToPerson(pId, dId)
            assert reply.statusCode == 204, reply.statusCode

            reply = cls.lunaClient.linkListToPerson(pId, inputListPersons)
            assert reply.statusCode == 204, reply.statusCode

        # remember last person data
        cls.sim_person = pId
        cls.sim_descriptor = dId

        # create group handler
        reply = fsmRequests.createHandler(handlers_examples.searchHandlerTestEvents(
            cls.name, 'groups', inputListDescriptors, inputListPersons, outputList
        ))
        assert reply.statusCode == 201, reply.statusCode
        handler_id = reply.json['handler_id']

        # send two fake events with another create_time, user_data, source, age and gender but same handler_id
        reply = fsmRequests.emitEvent(handler_id, personsImgs_search[0], {'user_data': "fake", 'source': "fake"})
        assert reply.statusCode == 201, reply.json
        reply = fsmRequests.emitEvent(handler_id, personsImgs_search[0], {'user_data': "fake", 'source': "fake",
                                                                          'tags': "fake"})
        assert reply.statusCode == 201, reply.json
        sleep(1)

        cls.start = datetime.now().isoformat('T').split('.')[0] + 'Z'

        reply = fsmRequests.emitEvent(handler_id, events_search[0], {'user_data': cls.name, 'source': cls.name,
                                                                     'tags': cls.name + ',' + cls.name + '1'})
        assert reply.statusCode == 201, reply.json
        cls.events['groups'] = reply.json['events'][0]

        reply = fsmRequests.createHandler(handlers_examples.searchHandlerTestEvents(
            cls.name, 'groups', inputListDescriptors, inputListPersons, outputList
        ))
        assert reply.statusCode == 201, reply.statusCode
        handler_id = reply.json['handler_id']

        reply = fsmRequests.emitEvent(handler_id, simEvents[0], {'user_data': cls.name, 'source': cls.name})
        assert reply.statusCode == 201, reply.json
        cls.events['similarity'] = reply.json['events'][0]

        sleep(1)
        cls.stop = datetime.now().isoformat('T').split('.')[0] + 'Z'

    def setUp(self):
        pass

    def assertSearch(self, result, filtersOk, filtersNOk):
        defaultFilters = {
            'handler_ids': result['handler_id'],
        }
        if any(f in chain(filtersOk, filtersNOk) for f in defaultFilters):
            defaultFilters = {}

        # TP - FP
        reply = fsmRequests.searchGroups({**defaultFilters, **filtersOk})
        self.assertEqual(reply.statusCode, 200, reply.json)
        self.assertEqual(reply.json['total'], 1, reply.json)
        self.assertEqual(reply.json['hits'][0]['descriptors'][0], result['id'], reply.json['hits'][0])

        # TN - FN
        reply = fsmRequests.searchGroups({**defaultFilters, **filtersNOk})
        self.assertEqual(reply.statusCode, 200, reply.statusCode)
        if 'page' in filtersNOk:
            self.assertEqual(len(reply.json['hits']), 0, len(reply.json['hits']))
        else:
            self.assertTrue(
                reply.json['total'] == 0 or all(hit['source'] == 'fake' for hit in reply.json['hits']),
                reply.json
            )

    def test_id(self):
        gId = self.events['groups']['group_id']
        reply = fsmRequests.getGroup(gId)
        self.assertEqual(reply.statusCode, 200, reply.statusCode)
        self.assertEqual(reply.json['source'], self.name, reply.json['source'])

    def test_time_filter(self):
        self.assertSearch(
            self.events['groups'],
            {
                'create_time__gt': self.start,
                'create_time__lt': self.stop,
            },
            {
                'create_time__gt': self.stop,
            }
        )

    def test_gender_filter(self):
        gender = round(self.events['groups']['extract']['attributes']['gender'])

        self.assertSearch(
            self.events['groups'],
            {
                'gender': gender
            },
            {
                'gender': int(not gender)
            }
        )

    def test_handler_filter(self):
        handler_id = self.events['groups']['handler_id']

        self.assertSearch(
            self.events['groups'],
            {
                'handler_ids': handler_id + ',' + str(uuid4()),

                'create_time__gt': self.start,
                'create_time__lt': self.stop
            },
            {
                'handler_ids': str(uuid4()) + ',' + str(uuid4()),

                'create_time__gt': self.start,
                'create_time__lt': self.stop
            }
        )

    def test_age_filter(self):
        age = int(self.events['groups']['extract']['attributes']['age'])
        ages = age, age + 1

        self.assertSearch(
            self.events['groups'],
            {
                'age__gt': ages[0],
                'age__lt': ages[1]
            },
            {
                'age__gt': ages[1]
            }
        )

    def test_source_filter(self):
        self.assertSearch(
            self.events['groups'],
            {
                'sources': self.name + ',' + 'test_Abudabi'
            },
            {
                'sources': 'test_Abudabi,test_Abudabi'
            }
        )

    def test_similarity_filter(self):
        sim = max(max(c['similarity'] for c in s['candidates']) for s in self.events['similarity']['search'])
        self.assertSearch(
            self.events['similarity'],
            {
                'similarity__gt': sim - 10 ** (-8),
                'similarity__lt': sim + 10 ** (-8)
            },
            {
                'similarity__lt': 0
            }
        )

    def test_sim_descriptor_filter(self):
        self.assertSearch(
            self.events['groups'],
            {
                'sim_descriptor': self.sim_descriptor
            },
            {
                'sim_descriptor': str(uuid4())
            }
        )

    def test_sim_person_filter(self):
        self.assertSearch(
            self.events['groups'],
            {
                'sim_person': self.sim_person
            },
            {
                'sim_person': str(uuid4())
            }
        )

    def test_sim_list_filter(self):
        self.assertSearch(
            self.events['groups'],
            {
                'sim_list': self.events['groups']['search'][0]['list_id'],

                'create_time__gt': self.start,
                'create_time__lt': self.stop,
            },
            {
                'sim_list': str(uuid4())
            }
        )

    def test_sim_user_data(self):
        self.assertSearch(
            self.events['groups'],
            {
                'sim_user_data': self.name,
                'create_time__gt': self.start,
            },
            {
                'sim_user_data': 'test_Abudabi',
                'create_time__gt': self.start,
            }
        )

    def test_pagination_filter(self):
        self.assertSearch(
            self.events['groups'],
            {
                'page_size': 1,
                'page': 1,
                'create_time__gt': self.start,
            },
            {
                'page_size': 1,
                'page': 2,
                'create_time__gt': self.start,
            }
        )

    def test_tag_filter(self):
        self.assertSearch(
            self.events['groups'],
            {
                'tags': self.name
            },
            {
                'tags': self.name[:-1]
            }
        )

    def test_tags_filter(self):
        self.assertSearch(
            self.events['groups'],
            {
                'tags': self.name + '1' + ',' + self.name
            },
            {
                'tags': self.name[:-1] + ',' + self.name
            }
        )

    def test_wrong_id(self):
        eId = '123'
        reply = fsmRequests.getEvent(eId)
        self.assertEqual(reply.statusCode, 404, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12021, 'detail': 'Page not found'}, reply.json)

    def test_wrong_time_filter(self):
        stop = start = 'Abudabi'
        reply = fsmRequests.searchGroups({'create_time__gt': start})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'create_time__gt'"},
                             reply.json)
        reply = fsmRequests.searchGroups({'create_time__lt': stop})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'create_time__lt'"},
                             reply.json)

    def test_wrong_gender_filter(self):
        gender = 'Abudabi'
        reply = fsmRequests.searchGroups({'gender': gender})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'gender'"},
                             reply.json)

    def test_wrong_handler_filter(self):
        handler_id = 'Abudabi'
        reply = fsmRequests.searchGroups({'handler_ids': handler_id})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'handler_ids'"},
                             reply.json)

    def test_wrong_age_filter(self):
        age__lt = age__gt = 'Abudabi'
        reply = fsmRequests.searchGroups({'age__gt': age__gt})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'age__gt'"},
                             reply.json)
        reply = fsmRequests.searchGroups({'age__lt': age__lt})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'age__lt'"},
                             reply.json)

    def test_wrong_similarity_filter(self):
        similarity__gt = 'Abudabi'
        reply = fsmRequests.searchGroups({'similarity__gt': similarity__gt})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'similarity__gt'"},
                             reply.json)

    def test_wrong_external_id_filter(self):
        external_id = 'Abudabi'
        reply = fsmRequests.searchGroups({'external_id': external_id})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'external_id'"},
                             reply.json)

    def test_wrong_sim_descriptor_filter(self):
        sim_descriptor = 'Abudabi'
        reply = fsmRequests.searchGroups({'sim_descriptor': sim_descriptor})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'sim_descriptor'"},
                             reply.json)

    def test_wrong_sim_person_filter(self):
        sim_person = 'Abudabi'
        reply = fsmRequests.searchGroups({'sim_person': sim_person})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'sim_person'"},
                             reply.json)

    def test_wrong_person_id_filter(self):
        person_id = 'Abudabi'
        reply = fsmRequests.searchGroups({'person_id': person_id})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'person_id'"},
                             reply.json)

    def test_wrong_page_filter(self):
        page = 'Abudabi'
        reply = fsmRequests.searchGroups({'page': page})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'page'"},
                             reply.json)

    def test_wrong_page_size_filter(self):
        page_size = 'Abudabi'
        reply = fsmRequests.searchGroups({'page_size': page_size})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'page_size'"},
                             reply.json)
