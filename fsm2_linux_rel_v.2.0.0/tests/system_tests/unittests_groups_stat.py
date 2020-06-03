from itertools import chain
from time import sleep
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from tests.system_tests import fsmRequests, base_test_class, handlers_examples, elasticRequests
from tests.system_tests.test_data_option import *

neededFields = {
    'aggregator': 'count',
    'group_by': '1m',
}


class TestStatGroups(base_test_class.BaseTest):
    name = 'test_visionlabs_test_stat_groups_class'
    start = None
    stop = None
    event = None
    events = {}
    handlers = {}
    event_batches_to_create = set()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if args[0] in cases:
            TestStatGroups.event_batches_to_create.add(cases[args[0]])
        else:
            TestStatGroups.event_batches_to_create.add('groups')

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

        # create handlers, events
        cls.start = datetime.now().isoformat('T').split('.')[0] + 'Z'
        for stat_type in cls.event_batches_to_create:
            reply = fsmRequests.createHandler(handlers_examples.searchHandlerTestEvents(
                cls.name, 'groups', inputListDescriptors, inputListPersons, outputList
            ))
            assert reply.statusCode == 201, reply.statusCode
            handler = reply.json['handler_id']
            cls.handlers[stat_type] = reply.json['handler_id']

            if stat_type == 'groups':
                reply = fsmRequests.emitEvent(handler, events_search[0],
                                              {'user_data': cls.name, 'source': cls.name,
                                               'tags': cls.name + ',' + cls.name + '1'})
                assert reply.statusCode == 201, reply.json
                sleep(10)
                reply = fsmRequests.emitEvent(handler, events_search[0],
                                              {'user_data': cls.name, 'source': cls.name,
                                               'tags': cls.name + ',' + cls.name + '1'})
                assert reply.statusCode == 201, reply.json
                cls.events[stat_type] = reply.json['events'][0]
            else:
                start = datetime(2017, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta()))

                stop = {
                    'monthOfYear': datetime(2018, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta())),
                    'dayOfYear': datetime(2018, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta())),
                    'dayOfMonth': datetime(2017, 2, 1, 0, 0, 0, tzinfo=timezone(timedelta())),
                    'dayOfWeek': datetime(2017, 1, 8, 0, 0, 0, tzinfo=timezone(timedelta())),
                    'hourOfDay': datetime(2017, 1, 2, 0, 0, 0, tzinfo=timezone(timedelta())),
                    'minuteOfDay': datetime(2017, 1, 2, 0, 0, 0, tzinfo=timezone(timedelta())),
                }[stat_type]

                delta = {
                    'monthOfYear': timedelta(days=31),
                    'dayOfYear': timedelta(days=1),
                    'dayOfMonth': timedelta(days=1),
                    'dayOfWeek': timedelta(days=1),
                    'hourOfDay': timedelta(hours=1),
                    'minuteOfDay': timedelta(minutes=1),
                }[stat_type]

                def uploadAsync(startPeriod, stopPeriod, deltaForPeriod):
                    current = startPeriod
                    dates = []
                    while current < stopPeriod:
                        dates.append(current)
                        current += deltaForPeriod

                    iterByDates = iter(dates)
                    from tornado import gen
                    import tornado.ioloop

                    @gen.coroutine
                    def upload(it):
                        for uploadDate in it:
                            reply = yield elasticRequests.emitGroupAsync(uploadDate.timestamp() * 1000, handler,
                                                                         cls.name)
                            assert reply.code < 300

                    tornado.ioloop.IOLoop.current().run_sync(lambda: [upload(iterByDates) for i in range(10)])

                uploadAsync(start, stop, delta)
        sleep(1)
        cls.stop = datetime.now().isoformat('T').split('.')[0] + 'Z'

    def setUp(self):
        pass

    def assertAgregate(self, result, filtersOk, filtersNOk=None):
        defaultFilters = {
            'aggregator': 'count',
            'group_by': '1d',

            'handler_ids': result['handler_id']
        }
        if any(f in chain(filtersOk, filtersNOk or {}) for f in defaultFilters):
            defaultFilters = {}

        # TP - FP
        reply = fsmRequests.statsGroups({**defaultFilters, **filtersOk})
        self.assertEqual(reply.statusCode, 200, reply.statusCode)
        self.assertEqual(reply.json['total'], 1, reply.json['total'])
        if {**defaultFilters, **filtersOk}['aggregator'] == 'count':
            self.assertEqual(reply.json['hits'][0][1], 2, reply.json['hits'][0][1])
        elif filtersOk['target'] == 'age':
            self.assertAlmostEqual(reply.json['hits'][0][1], result['extract']['attributes'][filtersOk['target']],
                                   msg=reply.json['hits'][0][1], delta=1)
        else:
            self.assertEqual(reply.json['hits'][0][1], result['extract']['attributes'][filtersOk['target']],
                             reply.json['hits'][0][1])

        if filtersNOk is not None:
            # TN - FN
            reply = fsmRequests.statsGroups({**defaultFilters, **filtersNOk})
            self.assertEqual(reply.statusCode, 200, reply.statusCode)
            self.assertEqual(reply.json['total'], 0, reply.json['total'])

    def test_count_aggregator(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'aggregator': 'count',
                'group_by': '1d',

                'handler_ids': self.events['groups']['handler_id']
            }
        )

    def test_max_age_aggregator(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'aggregator': 'max',

                'group_by': '1d',
                'target': 'age',
                'handler_ids': self.events['groups']['handler_id'],
            }
        )

    def test_avg_age_aggregator(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'aggregator': 'avg',

                'group_by': '1d',
                'target': 'age',
                'handler_ids': self.events['groups']['handler_id'],
            }
        )

    def test_min_age_aggregator(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'aggregator': 'min',

                'group_by': '1d',
                'target': 'age',
                'handler_ids': self.events['groups']['handler_id'],
            }
        )

    def test_min_gender_aggregator(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'target': 'gender',

                'aggregator': 'min',
                'group_by': '1d',
                'handler_ids': self.events['groups']['handler_id'],
            }
        )

    def test_group_by_edges(self):
        create_time__gt = '2017-01-01T00:00:00Z'
        for group_by_true, group_by_false, create_time__lt in (
                ('5s', '4s', '2017-01-01T01:00:00Z'),
                ('1m', '59s', '2017-01-02T00:00:00Z'),
                ('10m', '9m', '2017-02-01T00:00:00Z'),
                ('1h', '59m', '2018-01-01T00:00:00Z'),
                ('1d', '23h', '2020-01-01T00:00:00Z'),
        ):
            params = {'create_time__gt': create_time__gt, 'create_time__lt': create_time__lt,
                      'group_by': group_by_true, 'aggregator': 'count'}
            reply = fsmRequests.statsGroups(params)
            self.assertEqual(reply.statusCode, 200, reply.statusCode)

            params['group_by'] = group_by_false
            reply = fsmRequests.statsGroups(params)
            self.assertEqual(reply.statusCode, 400, reply.statusCode)
            self.assertDictEqual(reply.json,
                                 {'error_code': 12024, 'detail': "Group step '{}' is too low".format(group_by_false)},
                                 reply.json)

    def assertFrequencyGroupBy(self, reply, total, shift):
        self.assertEqual(reply.statusCode, 200, str(reply.statusCode) + ' ' + str(reply.json))
        self.assertEqual(reply.json['total'], total, reply.statusCode)
        self.assertEqual(reply.json['hits'], [[str(i), 1] for i in range(shift, shift + total)], reply.statusCode)

    def test_group_by_monthOfYear(self):
        params = {
            'aggregator': 'count',
            'group_by': 'monthOfYear',
            'sources': self.name,
            'handler_ids': self.handlers['monthOfYear'],
        }
        self.assertFrequencyGroupBy(fsmRequests.statsGroups(params), 12, 1)

    def test_group_by_dayOfYear(self):
        params = {
            'aggregator': 'count',
            'group_by': 'dayOfYear',
            'handler_ids': self.handlers['dayOfYear'],
            'sources': self.name,
        }
        self.assertFrequencyGroupBy(fsmRequests.statsGroups(params), 365, 1)

    def test_group_by_dayOfMonth(self):
        params = {
            'aggregator': 'count',
            'group_by': 'dayOfMonth',
            'handler_ids': self.handlers['dayOfMonth'],
            'sources': self.name,
        }
        self.assertFrequencyGroupBy(fsmRequests.statsGroups(params), 31, 1)

    def test_group_by_dayOfWeek(self):
        params = {
            'aggregator': 'count',
            'group_by': 'dayOfWeek',
            'handler_ids': self.handlers['dayOfWeek'],
            'sources': self.name,
        }
        self.assertFrequencyGroupBy(fsmRequests.statsGroups(params), 7, 1)

    def test_group_by_hourOfDay(self):
        params = {
            'aggregator': 'count',
            'group_by': 'hourOfDay',
            'handler_ids': self.handlers['hourOfDay'],
            'sources': self.name,
        }
        self.assertFrequencyGroupBy(fsmRequests.statsGroups(params), 24, 0)

    def test_group_by_minuteOfDay(self):
        params = {
            'aggregator': 'count',
            'group_by': 'minuteOfDay',
            'handler_ids': self.handlers['minuteOfDay'],
            'sources': self.name,
        }
        self.assertFrequencyGroupBy(fsmRequests.statsGroups(params), 1440, 0)

    def test_time_filter(self):
        self.assertAgregate(
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

        self.assertAgregate(
            self.events['groups'],
            {
                'gender': gender
            },
            {
                'gender': int(not gender)
            }
        )

    def test_handler_filter(self):

        self.assertAgregate(
            self.events['groups'],
            {
                'handler_ids': self.events['groups']['handler_id'] + ',' + str(uuid4()),

                'aggregator': 'count',
                'group_by': '1d'
            },
            {
                'handler_ids': str(uuid4()) + ',' + str(uuid4()),

                'aggregator': 'count',
                'group_by': '1d'
            }
        )

    def test_age_filter(self):
        age = int(self.events['groups']['extract']['attributes']['age'])
        ages = age, age + 1

        self.assertAgregate(
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
        self.assertAgregate(
            self.events['groups'],
            {
                'sources': self.name + ',' + 'test_Abudabi'
            },
            {
                'sources': 'test_Abudabi,test_Abudabi'
            }
        )

    def test_similarity_filter(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'similarity__gt': 1
            }
        )

    def test_sim_descriptor_filter(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'sim_descriptor': self.sim_descriptor
            },
            {
                'sim_descriptor': str(uuid4())
            }
        )

    def test_sim_person_filter(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'sim_person': self.sim_person
            },
            {
                'sim_person': str(uuid4())
            }
        )

    def test_sim_list_filter(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'sim_list': self.events['groups']['search'][0]['list_id']
            },
            {
                'sim_list': str(uuid4())
            }
        )

    def test_sim_user_data(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'sim_user_data': self.name
            },
            {
                'sim_user_data': 'test_Abudabi'
            }
        )

    def test_tag_filter(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'tags': self.name
            },
            {
                'tags': self.name[:-1]
            }
        )

    def test_tags_filter(self):
        self.assertAgregate(
            self.events['groups'],
            {
                'tags': self.name + '1' + ',' + self.name
            },
            {
                'tags': self.name[:-1] + ',' + self.name
            }
        )

    def test_no_group_by(self):
        reply = fsmRequests.statsGroups({'aggregator': 'count'})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12014, 'detail': "Required parameter 'group_by' not found"},
                             reply.json)

    def test_no_aggregator(self):
        reply = fsmRequests.statsGroups({'group_by': '1h'})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12014, 'detail': "Required parameter 'aggregator' not found"},
                             reply.json)

    def test_no_target(self):
        reply = fsmRequests.statsGroups({'group_by': '1h', 'aggregator': 'min'})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12014, 'detail': "Required parameter 'target' not found"},
                             reply.json)

    def test_wrong_aggregator(self):
        aggregator = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'aggregator': aggregator})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'aggregator'"},
                             reply.json)

    def test_wrong_group_by(self):
        group_by = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'group_by': group_by})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'group_by'"},
                             reply.json)

    def test_wrong_target(self):
        target = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'target': target})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'target'"},
                             reply.json)

    def test_wrong_time_filter(self):
        stop = start = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'create_time__gt': start})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'create_time__gt'"},
                             reply.json)
        reply = fsmRequests.statsGroups({**neededFields, 'create_time__lt': stop})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'create_time__lt'"},
                             reply.json)

    def test_wrong_gender_filter(self):
        gender = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'gender': gender})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'gender'"},
                             reply.json)

    def test_wrong_handler_filter(self):
        handler_id = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'handler_ids': handler_id})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'handler_ids'"},
                             reply.json)

    def test_wrong_age_filter(self):
        age__lt = age__gt = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'age__gt': age__gt})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'age__gt'"},
                             reply.json)
        reply = fsmRequests.statsGroups({**neededFields, 'age__lt': age__lt})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'age__lt'"},
                             reply.json)

    def test_wrong_similarity__gt_filter(self):
        similarity__gt = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'similarity__gt': similarity__gt})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'similarity__gt'"},
                             reply.json)

    def test_wrong_external_id_filter(self):
        external_id = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'external_id': external_id})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'external_id'"},
                             reply.json)

    def test_wrong_sim_descriptor_filter(self):
        sim_descriptor = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'sim_descriptor': sim_descriptor})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'sim_descriptor'"},
                             reply.json)

    def test_wrong_sim_person_filter(self):
        sim_person = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'sim_person': sim_person})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'sim_person'"},
                             reply.json)

    def test_wrong_person_id_filter(self):
        person_id = 'Abudabi'
        reply = fsmRequests.statsGroups({**neededFields, 'person_id': person_id})
        self.assertEqual(reply.statusCode, 400, reply.statusCode)
        self.assertDictEqual(reply.json, {'error_code': 12012, 'detail': "Bad query parameter 'person_id'"},
                             reply.json)
