import time

from tests.system_tests import base_test_class, fsmRequests, handlers_examples, config
from datetime import datetime
from time import sleep
from tests.system_tests.test_data_option import *


class LinkingTest(base_test_class.BaseTest):
    name = 'test_visionlabs_linking'
    events = {}
    handler = None

    @classmethod
    def setUpClass(cls):
        # create lists
        reply = cls.lunaClient.createList('descriptors', cls.name)
        assert reply.statusCode == 201, reply.body
        cls.inputListDescriptors = reply.body['list_id']

        reply = cls.lunaClient.createList('persons', cls.name)
        assert reply.statusCode == 201, reply.body
        cls.inputListPersons = reply.body['list_id']

        reply = cls.lunaClient.createList('descriptors', cls.name)
        assert reply.statusCode == 201, reply.body
        outputList = reply.body['list_id']
        cls.outputListDescriptors = outputList

        # create descriptors
        for d in descriptorsImgs_search:
            reply = cls.lunaClient.extractDescriptors(filename=d)
            assert reply.statusCode == 201, reply.body
            dId = reply.body["faces"][0]["id"]

            reply = cls.lunaClient.linkListToDescriptor(dId, cls.inputListDescriptors)
            assert reply.statusCode == 204, reply.body

        # create persons
        for p in personsImgs_search:
            reply = cls.lunaClient.createPerson(cls.name)
            assert reply.statusCode == 201, reply.body
            pId = reply.body['person_id']
            cls.personsToDelete += [pId]

            reply = cls.lunaClient.extractDescriptors(filename=p)
            assert reply.statusCode == 201, reply.body
            dId = reply.body["faces"][0]["id"]

            reply = cls.lunaClient.linkDescriptorToPerson(pId, dId)
            assert reply.statusCode == 204, reply.body

            reply = cls.lunaClient.linkListToPerson(pId, cls.inputListPersons)
            assert reply.statusCode == 204, reply.body

        # remember last person data
        cls.sim_person = pId
        cls.sim_descriptor = dId

    @classmethod
    def create_events(cls):
        # create handlers
        reply = fsmRequests.createHandler(handlers_examples.searchHandlerTestEvents(
            cls.name, 'groups', cls.inputListDescriptors, cls.inputListPersons, None, cls.outputListDescriptors
        ))
        assert reply.statusCode == 201, str(reply.json)
        cls.handler = reply.json['handler_id']

        # create events
        reply = fsmRequests.emitEvent(cls.handler, descriptorsImgs_search[0],
                                      {'user_data': 'fake', 'source': 'fake', 'tags': 'fake'})
        assert reply.statusCode == 201, str(reply.json)
        cls.events['fake'] = reply.json['events'][0]
        sleep(1)
        cls.start = datetime.now().isoformat('T').split('.')[0] + 'Z'
        reply = fsmRequests.emitEvent(cls.handler, events_search[0],
                                      {'user_data': cls.name, 'source': cls.name,
                                       'tags': cls.name + ',' + cls.name + '1'})

        assert reply.statusCode == 201, str(reply.json)
        cls.events['true'] = reply.json['events'][0]
        sleep(1)
        cls.stop = datetime.now().isoformat('T').split('.')[0] + 'Z'

    def attach_objects_to_list(self, linker_object, list_type):
        assert linker_object in ('events', 'groups')
        assert list_type in ('descriptors', 'persons')
        self.create_events()
        filters_batches = {
            'gender': {
                'true': {'gender': 1},
                'false': {'gender': 0, 'create_time__gt': self.start, 'create_time__lt': self.stop},
                'both': {'handler_ids': [self.handler]}
            },
            'create_time': {
                'true': {'create_time__gt': self.start, 'create_time__lt': self.stop},
                'false': {'create_time__gt': self.stop},
                'both': {'handler_ids': [self.handler]}
            },
            'tag': {
                'true': {'tags': [self.name]},
                'false': {'tags': [self.name[:-1]]},
                'both': {'handler_ids': [self.handler]}
            },
            'tags': {
                'true': {'tags': [self.name, self.name + '1']},
                'false': {'tags': [self.name[:-1], self.name + '1']},
                'both': {'handler_ids': [self.handler]}
            },
            'age': {
                'true': {
                    'age__lt': self.events['true']['extract']['attributes']['age'] + 1,
                    'age__gt': self.events['true']['extract']['attributes']['age'] - 1
                },
                'false': {'age__gt': self.events['true']['extract']['attributes']['age'] + 1},
                'both': {'handler_ids': [self.handler]}
            },
            'similarity': {
                'true': {
                    'similarity__gt': min(c['similarity'] for s in self.events['true']['search'] for c in s['candidates']) - 10 ** -3,
                    'similarity__lt': min(c['similarity'] for s in self.events['true']['search'] for c in s['candidates']) + 10 ** -3,
                },
                'false': {'similarity__lt': 0},
                'both': {'handler_ids': [self.handler]}
            },
        }
        task_ids, list_ids = {}, {}
        for sub_name in filters_batches:
            filters_batch = filters_batches[sub_name]
            for mode in ('true', 'false'):
                alias = sub_name + '_' + mode
                # create list
                reply = self.lunaClient.createList(list_type, self.name + '_' + alias)
                self.assertTrue(reply.success, reply.body)
                list_id = reply.body['list_id']
                LinkingTest.listsToDelete.append(list_id)

                task = {
                    'object': linker_object,
                    'list_id': list_id,
                    'list_type': list_type,
                    # 'list_data': 'test_events_to_descriptors_list',
                    'description': self.name,
                    'filters': {**filters_batch['both'], **filters_batch[mode]}
                }
                reply = fsmRequests.createTaskLinker(task)
                self.assertEqual(reply.statusCode, 202, str(reply.json))
                task_ids[alias] = reply.json['task_id']
                list_ids[alias] = list_id
                sleep(1)

        self.wait_tasks_ready(task_ids.values())

        for sub_name in filters_batches:
            for mode in ('true', 'false'):
                alias = sub_name + '_' + mode
                list_id = list_ids[alias]
                task_id = task_ids[alias]
                with self.subTest(alias):
                    # check done task
                    reply = fsmRequests.getDoneTask(task_id)
                    self.assertEqual(reply.json['type'], 'linker')
                    self.assertEqual(reply.json['status'], 'done')
                    self.assertEqual(reply.json['progress'], 1)
                    if mode == 'true':
                        self.assertEqual(reply.json['result'], {'success': {'succeed': 1, 'failed': 0}})
                    else:
                        self.assertEqual(reply.json['result'], {'success': {'succeed': 0, 'failed': 0}})


                    reply = self.lunaClient.getList(list_id)
                    self.assertEqual(reply.statusCode, 200, reply.body)

                    if list_type == 'descriptors':
                        if mode == 'true':
                            self.assertEqual(len(reply.body['descriptors']), 1, reply.body)
                            self.assertEqual(reply.body['descriptors'][0]['id'], self.events[mode]['id'], reply.body)
                        else:
                            self.assertTrue(len(reply.body['descriptors']) == 0, reply.body)
                    else:
                        if mode == 'true':
                            self.assertEqual(len(reply.body['persons']), 1, reply.body)
                            self.assertEqual(len(reply.body['persons'][0]['descriptors']), 1, reply.body)
                            self.assertEqual(reply.body['persons'][0]['descriptors'][0], self.events[mode]['id'],
                                             reply.body)
                            self.personsToDelete.append(reply.body['persons'][0]['id'])
                        else:
                            self.assertTrue(len(reply.body['persons']) == 0, reply.body)

    def create_list(self, list_type, *, with_object=False):
        # create list
        reply = self.lunaClient.createList(list_type, self.name)
        self.assertEqual(reply.statusCode, 201, reply.body)
        list_id = reply.body['list_id']
        LinkingTest.listsToDelete.append(list_id)

        if with_object:
            # create descriptor
            reply = self.lunaClient.extractDescriptors(filename=events_search[0], warpedImage=True)
            self.assertEqual(reply.statusCode, 201, reply.body)
            dId = reply.body["faces"][0]["id"]

            # attach descriptor
            if list_type == 'descriptors':
                reply = self.lunaClient.linkListToDescriptor(dId, list_id)
                self.assertEqual(reply.statusCode, 204, reply.body)
            else:
                reply = self.lunaClient.createPerson(self.name)
                self.assertEqual(reply.statusCode, 201, reply.body)
                pId = reply.body['person_id']
                LinkingTest.personsToDelete.append(pId)

                reply = self.lunaClient.linkDescriptorToPerson(pId, dId)
                self.assertEqual(reply.statusCode, 204, reply.body)

                reply = self.lunaClient.linkListToPerson(pId, list_id)
                self.assertEqual(reply.statusCode, 204, reply.body)
        return list_id

    def test_events_to_descriptors_list(self):
        self.attach_objects_to_list('events', 'descriptors')

    def test_events_to_persons_list(self):
        self.attach_objects_to_list('events', 'persons')

    def test_groups_to_persons_list(self):
        self.attach_objects_to_list('groups', 'persons')

    def test_groups_to_persons_list_inconsistent_group(self):
        def prepare_fsm_objects():
            # create handler
            handler = dict(
                name=self.name,
                type="extract",
                multiple_faces_policy=0,
                grouping_policy=dict(
                    ttl=10,
                    grouper=2,
                    threshold=0
                )
            )
            reply = fsmRequests.createHandler(handler)
            self.assertEqual(reply.statusCode, 201, "Cannot create handler '{}'".format(handler))
            handler_id = reply.json['handler_id']

            # emit events
            for i in range(3):
                reply = fsmRequests.emitEvent(handler_id, events[0])
                self.assertEqual(reply.statusCode, 201, "Cannot emit event '{}'".format(events_search[0]))
            group_ttl_start = time.time()
            descriptor_id = reply.json['events'][0]['descriptor_id']
            return handler_id, descriptor_id, group_ttl_start

        def create_incompatible_event(descriptor_id):
            # make one of group descriptors attached to a person
            reply = self.lunaClient.createPerson(self.name)
            self.assertTrue(reply.success, reply.body)
            person_id = reply.body['person_id']
            LinkingTest.personsToDelete.append(person_id)
            reply = self.lunaClient.linkDescriptorToPerson(person_id, descriptor_id, 'attach')
            self.assertTrue(reply.success, reply.body)

        def create_person_list():
            # create person list
            reply = self.lunaClient.createList('persons', self.name)
            self.assertTrue(reply.success, reply.body)
            list_id = reply.body['list_id']
            LinkingTest.listsToDelete.append(list_id)
            return list_id

        def create_tasks_jsons(list_id, handler_id):
            # create tasks jsons
            task_objects = ('events', 'groups')
            tasks = {task_object: {
                'description': self.name,
                'object': task_object,
                'list_id': list_id,
                'list_type': 'persons',
                'filters': {'handler_ids': [handler_id]}
            } for task_object in task_objects}
            return tasks

        def events_test(task):
            # execute events task
            with self.subTest(task_object='event'):
                reply = fsmRequests.createTaskLinker(task)
                self.assertEqual(reply.statusCode, 202, reply.json)
                task_id = reply.json['task_id']
                self.wait_tasks_ready([task_id])

                # check events task result
                reply = fsmRequests.getDoneTask(task_id)
                self.assertEqual(reply.statusCode, 200, reply.json)
                self.assertDictEqual(
                    {
                        'success': {
                            'succeed': 3,
                            'failed': 0
                        }
                    },
                    reply.json['result'],
                    reply.json['result']
                )

        def groups_test(task):
            # execute groups task
            with self.subTest(task_object='groups'):
                reply = fsmRequests.createTaskLinker(task)
                self.assertEqual(reply.statusCode, 202, reply.json)
                task_id = reply.json['task_id']
                self.wait_tasks_ready([task_id])

                # check groups task result
                reply = fsmRequests.getDoneTask(task_id)
                self.assertEqual(reply.statusCode, 200, reply.json)
                self.assertDictEqual(
                    {
                        'succeed': 0,
                        'failed': 0
                    }
                    ,
                    reply.json['result']['success'],
                    reply.json['result']['success']
                )
                self.assertIn('errors', reply.json['result'], reply.json)
                self.assertEqual(1, reply.json['result']['errors']['total'], reply.json)
                self.assertEqual(15007, reply.json['result']['errors']['errors'][0]['error_code'], reply.json)

        handler_id, descriptor_id, group_ttl_start = prepare_fsm_objects()
        create_incompatible_event(descriptor_id)
        list_id = create_person_list()
        tasks = create_tasks_jsons(list_id, handler_id)

        # wait synchronise events
        sleep(1 - time.time() + group_ttl_start)

        events_test(tasks['events'])
        # now all of three descriptors have persons, but the group was not updated

        # wait close groups
        sleep(10 - time.time() + group_ttl_start)
        groups_test(tasks['groups'])

    def test_list_to_list(self):
        task_ids, list_ids = {}, {}
        for list_type in ('descriptors', 'persons'):
            for new_list_type in ('descriptors', 'persons'):
                alias = list_type + '_' + new_list_type
                list_id = self.create_list(list_type, with_object=True)
                new_list_id = self.create_list(new_list_type, with_object=False)

                task = {
                    'object': 'luna_list',
                    'list_id': new_list_id,
                    'list_type': new_list_type,
                    # 'list_data': 'test_events_to_descriptors_list',
                    'description': self.name,
                    'filters': {'list_id': list_id}
                }
                reply = fsmRequests.createTaskLinker(task)
                self.assertEqual(reply.statusCode, 202, str(reply.json))
                task_ids[alias] = reply.json['task_id']
                list_ids[alias] = list_id, new_list_id

        for list_type in ('descriptors', 'persons'):
            for new_list_type in ('descriptors', 'persons'):
                alias = list_type + '_' + new_list_type
                list_id, new_list_id = list_ids[alias]
                task_id = task_ids[alias]
                with self.subTest(alias):
                    for i in range(10):
                        reply = fsmRequests.getTaskInProgress(task_id)
                        if reply.statusCode == 303:
                            break
                        sleep(0.5)
                        self.assertEqual(reply.statusCode, 200, str(reply.json))
                    else:
                        self.fail("Task not done")

                    # check done task
                    reply = fsmRequests.getDoneTask(task_id)
                    self.assertEqual(reply.json['type'], 'linker')
                    self.assertEqual(reply.json['status'], 'done')
                    self.assertEqual(reply.json['progress'], 1)
                    self.assertEqual(reply.json['result'], {'success': {'succeed': 1, 'failed': 0}})

                    # check results
                    reply = self.lunaClient.getList(list_id)
                    self.assertEqual(reply.statusCode, 200, reply.body)
                    list_data = reply.body

                    reply = self.lunaClient.getList(new_list_id)
                    self.assertEqual(reply.statusCode, 200, reply.body)
                    new_list_data = reply.body

                    if list_type == new_list_type:
                        self.assertEqual(list_data[list_type], new_list_data[new_list_type], new_list_data)
                    elif new_list_type == 'descriptors':
                        self.assertEqual(len(new_list_data['descriptors']), 1, new_list_data)
                        self.assertEqual(
                            new_list_data['descriptors'][0]['id'],
                            list_data['persons'][0]['descriptors'][0],
                            new_list_data
                        )
                    elif new_list_type == 'persons':
                        self.assertEqual(len(new_list_data['persons']), 1, new_list_data)
                        self.assertEqual(len(new_list_data['persons'][0]['descriptors']), 1, new_list_data)
                        self.assertEqual(
                            new_list_data['persons'][0]['descriptors'][0],
                            list_data['descriptors'][0]['id'],
                            new_list_data
                        )
                    else:
                        self.fail('Unbelievable')

                    if new_list_type == 'persons':
                        self.personsToDelete.append(new_list_data['persons'][0]['id'])

    def test_wrong_schema(self):
        task = {
            'object': 'luna_list',
            # 'list_id': 'e65c7692-8682-48e0-81e6-e2cbe023afbe',
            'list_type': 'descriptors',
            # 'list_data': 'test_events_to_descriptors_list',
            'description': self.name,
            'filters': {'list_id': 'e65c7692-8682-48e0-81e6-e2cbe023afbe'}
        }
        reply = fsmRequests.createTaskLinker(task)
        self.assertEqual(reply.statusCode, 400, str(reply.json))
        self.assertEqual(reply.json['error_code'], 12019, str(reply.json))

    def test_wrong_list(self):
        task = {
            'object': 'luna_list',
            'list_id': 'e65c7692-8682-48e0-81e6-e2cbe023afbe',
            'list_type': 'descriptors',
            # 'list_data': 'test_events_to_descriptors_list',
            'description': self.name,
            'filters': {'list_id': 'e65c7692-8682-48e0-81e6-e2cbe023afbe'}
        }
        reply = fsmRequests.createTaskLinker(task)
        self.assertEqual(reply.statusCode, 202, str(reply.json))
        task_id = reply.json['task_id']

        self.wait_tasks_ready([task_id])

        # check done task
        reply = fsmRequests.getDoneTask(task_id)
        self.assertEqual(reply.json['type'], 'linker')
        self.assertEqual(reply.json['status'], 'failed')
        self.assertEqual(reply.json['progress'], 0)
        self.assertTrue('success' not in reply.json['result'])

    def test_data_field(self):
        self.create_events()
        tasks = [
            {
                'object': 'events',
                'list_data': 'test_visionlabs_linker_data_field',
                'list_type': list_type,
                'description': self.name,
                'filters': {'handler_ids': [self.handler]}
            } for list_type in ('persons', 'descriptors')
        ] + [
            {
                'object': 'luna_list',
                'list_data': 'test_visionlabs_linker_data_field',
                'list_type': list_type,
                'description': self.name,
                'filters': {'list_id': self.outputListDescriptors}
            } for list_type in ('persons', 'descriptors')
        ]
        task_ids = []
        for task in tasks:
            reply = fsmRequests.createTaskLinker(task)
            self.assertEqual(reply.statusCode, 202, str(reply.json))
            task_ids += [reply.json['task_id']]

        for task_id in task_ids:
            for i in range(10):
                reply = fsmRequests.getTaskInProgress(task_id)
                if reply.statusCode == 303:
                    break
                sleep(0.5)
                self.assertEqual(reply.statusCode, 200, str(reply.json))
            else:
                self.fail("Task {} not done".format(task_id))

        for task_id in task_ids:
            # check done task
            msg = tasks[task_ids.index(task_id)]['object'] + ' to ' + tasks[task_ids.index(task_id)]['list_type']
            with self.subTest(msg):
                reply = fsmRequests.getDoneTask(task_id)
                self.assertIn('list_id', reply.json['task'], str(reply.json))
                LinkingTest.listsToDelete += [reply.json['task']['list_id']]

    def test_additional_fields(self):
        perfect_task = {
            'object': 'luna_list',
            # 'list_id': 'e65c7692-8682-48e0-81e6-e2cbe023afbe',
            'list_type': 'descriptors',
            'list_data': 'test_events_to_descriptors_list',
            'description': self.name,
            'filters': {'list_id': 'e65c7692-8682-48e0-81e6-e2cbe023afbe'}
        }
        self.corrupt_test(perfect_task, ('', 'filters'), fsmRequests.createTaskLinker)
