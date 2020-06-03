from itertools import chain
from tests.system_tests import base_test_class, fsmRequests
from tests.system_tests.handlers_examples import searchHandlerTestEvents
from tests.system_tests.test_data_option import *
from datetime import datetime
from time import sleep


# todo speedup
class CrossMatchTest(base_test_class.BaseTest):
    name = 'test_visionlabs_cross_match'
    events = []
    handler = None
    tasks_to_add = set()
    tasks_ids = {}
    tasks_results = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        CrossMatchTest.tasks_to_add.add(args[0])

    @classmethod
    def cases(cls):
        return {
            "test_events_to_descriptors": [{
                "objects": 'events',
                "filters": {"handler_ids": [cls.handler]}
            }],
            "test_groups_to_descriptors": [{
                "objects": 'groups',
                "filters": {"handler_ids": [cls.handler]}
            }],
            "test_list_descriptors_to_descriptors": [{
                "objects": 'luna_list',
                "filters": {"list_id": cls.outputListDescriptors}
            }],
            "test_list_persons_to_descriptors": [{
                "objects": 'luna_list',
                "filters": {"list_id": cls.outputListPersons}
            }],
            "test_events_to_persons": [{
                "objects": 'events',
                "filters": {"handler_ids": [cls.handler]},
                "target": 'persons'
            }],
            "test_groups_to_persons": [{
                "objects": 'groups',
                "filters": {"handler_ids": [cls.handler]},
                "target": 'persons'
            }],
            "test_list_descriptors_to_persons": [{
                "objects": 'luna_list',
                "filters": {"list_id": cls.outputListDescriptors},
                "target": 'persons'
            }],
            "test_list_persons_to_persons": [{
                "objects": 'luna_list',
                "filters": {"list_id": cls.outputListPersons},
                "target": 'persons'
            }],
            "test_filters_ok": [
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler, uuid]}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "create_time__gt": cls.start}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "create_time__lt": cls.stop}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "sources": [cls.name, 'Abudabi']}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "tags": [cls.name]}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "tags": [cls.name, cls.name + '1']}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "gender": 1}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "gender": 0}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler],
                                "age__gt": int(cls.events[0]['extract']['attributes']['age'])}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler],
                                "age__lt": int(cls.events[0]['extract']['attributes']['age']) + 1}
                },
            ],
            "test_filters_nok": [
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [uuid]}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "create_time__lt": cls.start}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "create_time__gt": cls.stop}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "sources": ['Abudabi']}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "tags": [cls.name[:-1]]}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler], "tags": [cls.name, cls.name[:-1]]}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler],
                                "age__gt": int(max(e['extract']['attributes']['age'] for e in cls.events)) + 1}
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handler],
                                "age__lt": int(min(e['extract']['attributes']['age'] for e in cls.events)) - 1}
                },
            ],
            "test_limit": [
                {
                    "objects": "events",
                    "filters": {"handler_ids": [cls.handler]},
                    "limit": limit
                }
                for limit in range(6)
            ],
            "test_wrong_list_reference": [{
                "objects": 'luna_list',
                "filters": {'list_id': uuid}
            }]
        }

    @classmethod
    def add_tasks(cls):
        for test_name in cls.tasks_to_add:
            if test_name in cls.cases():
                cls.tasks_ids[test_name] = [cls.add_task(**task_kwargs) for task_kwargs in cls.cases()[test_name]]
        cls.wait_tasks_ready(chain(*cls.tasks_ids.values()))
        for test_name in cls.tasks_to_add:
            if test_name in cls.cases():
                cls.tasks_results[test_name] = [cls.get_task(task_id) for task_id in cls.tasks_ids[test_name]]

    @classmethod
    def setUpClass(cls):
        # create lists
        reply = cls.lunaClient.createList('descriptors', cls.name)
        assert reply.statusCode == 201, reply.body
        cls.listDescriptors = reply.body['list_id']
        cls.listsToDelete += [cls.listDescriptors]

        reply = cls.lunaClient.createList('persons', cls.name)
        assert reply.statusCode == 201, reply.body
        cls.listPersons = reply.body['list_id']
        cls.listsToDelete += [cls.listPersons]

        reply = cls.lunaClient.createList('descriptors', cls.name)
        assert reply.statusCode == 201, reply.body
        cls.outputListDescriptors = reply.body['list_id']

        reply = cls.lunaClient.createList('persons', cls.name)
        assert reply.statusCode == 201, reply.body
        cls.outputListPersons = reply.body['list_id']

        # create persons
        for personImgs in personsImgs:
            # create person
            reply = cls.lunaClient.createPerson(cls.name)
            assert reply.statusCode == 201, reply.statusCode
            pId = reply.body['person_id']
            cls.personsToDelete += [pId]

            # link to persons list
            reply = cls.lunaClient.linkListToPerson(pId, cls.listPersons)
            assert reply.statusCode == 204, reply.statusCode

            for img in personImgs:
                # extract descriptor
                reply = cls.lunaClient.extractDescriptors(filename=img)
                assert reply.statusCode == 201, reply.statusCode
                dId = reply.body["faces"][0]["id"]

                # link to descriptors list
                reply = cls.lunaClient.linkListToDescriptor(dId, cls.listDescriptors)
                assert reply.statusCode == 204, reply.statusCode

                # link to person
                reply = cls.lunaClient.linkDescriptorToPerson(pId, dId)
                assert reply.statusCode == 204, reply.statusCode

        handler = {
            "name": cls.name,
            "type": "extract",
            'multiple_faces_policy': 1,
            "extract_policy": {
                "estimate_attributes": 1,
            },
            "grouping_policy": {
                "ttl": 10,
                "grouper": 2,
                "threshold": 0.9,
            },
            "descriptor_policy": {
                "attach_policy": [{
                    "list_id": cls.outputListDescriptors
                }]
            },
            "person_policy": {
                "create_person_policy": {
                    "create_person": 1,
                    "attach_policy": [{
                        "list_id": cls.outputListPersons
                    }]
                }
            }
        }

        reply = fsmRequests.createHandler(handler)
        assert reply.statusCode == 201, reply.json
        cls.handler = reply.json['handler_id']

        cls.start = datetime.now().isoformat('T').split('.')[0] + 'Z'
        sleep(1)
        for img in events:
            reply = fsmRequests.emitEvent(
                cls.handler,
                img,
                {
                    'user_data': cls.name,
                    'source': cls.name,
                    'tags': cls.name + ',' + cls.name + '1'
                }
            )
            assert reply.statusCode == 201, reply.json
            cls.events.append(reply.json['events'][0])
        sleep(1)
        cls.stop = datetime.now().isoformat('T').split('.')[0] + 'Z'

        cls.add_tasks()

    @classmethod
    def add_task(cls, objects, filters, limit=5, threshold=0, target='descriptors'):
        task = {
            "references": {
                "objects": objects,
                "filters": filters
            },
            "candidates": {
                "list_id": cls.listDescriptors if target == 'descriptors' else cls.listPersons
            },
            "description": cls.name,
            "threshold": threshold,
            "limit": limit
        }
        reply = fsmRequests.createTaskCrossMatcher(task)
        assert reply.statusCode == 202, reply.json
        return reply.json['task_id']

    @classmethod
    def get_task(cls, task_id):
        reply = fsmRequests.getDoneTask(task_id)
        assert reply.statusCode == 200, reply.json
        return reply.json

    def assert_result_descriptors(self, result, limit=5):
        result_limit = limit if 1 <= limit <= 5 else 3 if limit < 1 else 5
        self.assertEqual(len(result['result']['success']), 3, result)
        [self.assertEqual(len(res['candidates']), result_limit, res) for res in result['result']['success']]
        [
            self.assertGreaterEqual(res['candidates'][i]['similarity'], 0.5, res)
            for res in result['result']['success']
            for i in range(2 if limit > 1 else 1)
        ]

    def assert_result_persons(self, result):
        self.assertEqual(len(result['result']['success']), 3, result)
        [self.assertEqual(len(res['candidates']), 3, res) for res in result['result']['success']]
        [
            self.assertGreaterEqual(res['candidates'][i]['similarity'], 0.5, res)
            for res in result['result']['success']
            for i in range(1)
        ]

    def test_events_to_descriptors(self):
        result = self.tasks_results['test_events_to_descriptors'][0]
        self.assert_result_descriptors(result)

    def test_groups_to_descriptors(self):
        result = self.tasks_results['test_groups_to_descriptors'][0]
        self.assert_result_descriptors(result)

    def test_list_descriptors_to_descriptors(self):
        result = self.tasks_results['test_list_descriptors_to_descriptors'][0]
        self.assert_result_descriptors(result)

    def test_list_persons_to_descriptors(self):
        result = self.tasks_results['test_list_persons_to_descriptors'][0]
        self.assert_result_descriptors(result)

    def test_events_to_persons(self):
        result = self.tasks_results['test_events_to_persons'][0]
        self.assert_result_persons(result)

    def test_groups_to_persons(self):
        result = self.tasks_results['test_groups_to_persons'][0]
        self.assert_result_persons(result)

    def test_list_descriptors_to_persons(self):
        result = self.tasks_results['test_list_descriptors_to_persons'][0]
        self.assert_result_persons(result)

    def test_list_persons_to_persons(self):
        result = self.tasks_results['test_list_persons_to_persons'][0]
        self.assert_result_persons(result)

    def test_filters_ok(self):
        for i in range(len(self.tasks_results['test_filters_ok'])):
            result = self.tasks_results['test_filters_ok'][i]
            with self.subTest(('true', self.cases()['test_filters_ok'][i]['filters'])):
                self.assertGreaterEqual(len(result['result']['success']), 1, result)

    def test_filters_nok(self):
        for i in range(len(self.tasks_results['test_filters_nok'])):
            result = self.tasks_results['test_filters_nok'][i]
            with self.subTest(('true', self.cases()['test_filters_nok'][i]['filters'])):
                self.assertEqual(len(result['result']['success']), 0, result)

    def test_limit(self):
        results = self.tasks_results['test_limit']
        for i in range(len(results)):
            with self.subTest(limit=i):
                self.assert_result_descriptors(results[i], i)

    def test_wrong_list_reference(self):
        task_id = self.add_task('luna_list', {'list_id': uuid})
        self.wait_tasks_ready([task_id])
        reply = fsmRequests.getDoneTask(task_id)
        self.assertEqual(reply.statusCode, 200, reply.json)
        self.assertEqual(reply.json['status'], 'failed', reply.json)
        self.assertEqual(reply.json['result']['errors']['total'], 1, reply.json)
        self.assertEqual(reply.json['result']['errors']['errors'][0]['error_code'], 11007, reply.json)

    def test_wrong_json(self):
        task = {
            "references": {
                "objects": "events",
                "filters": {"filter_not_exist": "value"}
            },
            "candidates": {
                "list_id": uuid
            },
            "description": self.name,
            "threshold": 0,
            "limit": 5
        }
        reply = fsmRequests.createTaskCrossMatcher(task)
        self.assertEqual(reply.statusCode, 400, reply.json)
        self.assertEqual(reply.json['error_code'], 12019, reply.json)

    def test_wrong_list_candidate(self):
        task = {
            "references": {
                "objects": "events",
                "filters": {"handler_ids": [self.handler]}
            },
            "candidates": {
                "list_id": uuid
            },
            "description": self.name,
            "threshold": 0,
            "limit": 5
        }
        reply = fsmRequests.createTaskCrossMatcher(task)
        self.assertEqual(reply.statusCode, 202, reply.json)
        task_id = reply.json['task_id']
        self.wait_tasks_ready([task_id])
        reply = fsmRequests.getDoneTask(task_id)
        self.assertEqual(reply.statusCode, 200, reply.json)
        self.assertEqual(reply.json['status'], 'failed', reply.json)
        self.assertEqual(reply.json['result']['errors']['total'], 1, reply.json)
        self.assertEqual(reply.json['result']['errors']['errors'][0]['error_code'], 11007, reply.json)

    def test_additional_fields_in_json(self):
        perfect_task = {
            "references": {
                "objects": "events",
                "filters": {"handler_ids": [self.handler]}
            },
            "candidates": {
                "list_id": uuid
            },
            "description": self.name,
            "threshold": 0,
            "limit": 5
        }
        self.corrupt_test(perfect_task, ('', 'references', 'candidates', 'references.filters'),
                          fsmRequests.createTaskCrossMatcher)


class CrossMatchSimTest(base_test_class.BaseTest):
    """
    Create lists (d&p) with image A.

    Spam events A and B (with 2 groups creation).

    Match them with lists with similarity (A<->B) filter.

    Check that reference is only one.
    """
    name = "test_visionlabs_cross_match_similarity"
    imgs = personsImgs_search[-2:]
    events = []
    listDescriptors = listPersons = None

    @classmethod
    def setUpClass(cls):
        # create lists
        reply = cls.lunaClient.createList('descriptors', cls.name)
        assert reply.statusCode == 201, reply.body
        cls.listDescriptors = reply.body['list_id']
        cls.listsToDelete += [cls.listDescriptors]

        reply = cls.lunaClient.createList('persons', cls.name)
        assert reply.statusCode == 201, reply.body
        cls.listPersons = reply.body['list_id']
        cls.listsToDelete.append(cls.listPersons)

        # create person
        reply = cls.lunaClient.createPerson(cls.name)
        assert reply.statusCode == 201, reply.statusCode
        pId = reply.body['person_id']
        cls.personsToDelete += [pId]

        # link to persons list
        reply = cls.lunaClient.linkListToPerson(pId, cls.listPersons)
        assert reply.statusCode == 204, reply.statusCode

        # extract descriptor
        reply = cls.lunaClient.extractDescriptors(filename=cls.imgs[0])
        assert reply.statusCode == 201, reply.statusCode
        dId = reply.body["faces"][0]["id"]

        # link to descriptors list
        reply = cls.lunaClient.linkListToDescriptor(dId, cls.listDescriptors)
        assert reply.statusCode == 204, reply.statusCode

        # link to person
        reply = cls.lunaClient.linkDescriptorToPerson(pId, dId)
        assert reply.statusCode == 204, reply.statusCode

        # create handler
        handler = searchHandlerTestEvents(cls.name, 'groups', cls.listDescriptors, cls.listPersons)
        handler['grouping_policy']['threshold'] = 1
        reply = fsmRequests.createHandler(handler)
        assert reply.statusCode == 201, reply.json
        cls.handler = reply.json['handler_id']

        # emit events
        for img in cls.imgs:
            reply = fsmRequests.emitEvent(
                cls.handler,
                img,
                {
                    'user_data': cls.name,
                    'source': cls.name,
                    'tags': cls.name + ',' + cls.name + '1'
                }
            )
            assert reply.statusCode == 201, reply.json
            cls.events.append(reply.json['events'][0])
        sleep(10)

    @classmethod
    def add_task(cls, objects, filters, target='descriptors'):
        task = {
            "references": {
                "objects": objects,
                "filters": filters
            },
            "candidates": {
                "list_id": cls.listDescriptors if target == 'descriptors' else cls.listPersons
            },
            "description": cls.name,
            "threshold": 0
        }
        reply = fsmRequests.createTaskCrossMatcher(task)
        assert reply.statusCode == 202, reply.json
        return reply.json['task_id']

    @classmethod
    def get_task(cls, task_id):
        reply = fsmRequests.getDoneTask(task_id)
        assert reply.statusCode == 200, reply.json
        return reply.json

    def test_similarity(self):
        similarity = self.events[1]['search'][0]['candidates'][0]['similarity']
        simfilters = {
            "true": {
                "similarity__gt": similarity - 10 ** -3,
                "similarity__lt": similarity + 10 ** -3
            },
            "false": {"similarity__lt": 0.0},
            "both": {"handler_ids": [self.handler]}
        }

        # setup tasks
        tasks_ids = {}
        for ref in ("events", "groups"):
            for cand in ("descriptors", "persons"):
                for flag in ("true", "false"):
                    tasks_ids[(ref, cand, flag)] = self.add_task(ref, {**simfilters[flag], **simfilters['both']}, cand)
        self.wait_tasks_ready(tasks_ids.values())
        done_tasks = {subtest: self.get_task(task_id) for subtest, task_id in tasks_ids.items()}
        # check tasks
        for (ref, cand, flag), done_task in done_tasks.items():
            with self.subTest(obj=ref, candidates=cand, flag=flag):
                expected_references_count = flag is "true"
                self.assertEqual(len(done_task['result']['success']), expected_references_count, str(done_tasks[(ref, cand, flag)]))
