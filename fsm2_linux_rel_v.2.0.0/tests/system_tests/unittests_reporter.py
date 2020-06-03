from io import BytesIO
from itertools import chain
from time import sleep
from zipfile import ZipFile

from tests.system_tests import fsmRequests
from tests.system_tests.base_test_class import BaseTest
from tests.system_tests.config import USE_LATEX, FSM2_API_VERSION
from tests.system_tests.test_data_option import *


class ReporterTest(BaseTest):
    name = 'test_visionlabs_reporter'
    events = []
    handlers = []

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

        handlers = [
            {
                "name": cls.name,
                "type": "extract",
                'multiple_faces_policy': 1,
                "extract_policy": {
                    "estimate_attributes": ea,
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
            } for ea in range(2)
        ]

        for handler_type, handler in enumerate(handlers):
            reply = fsmRequests.createHandler(handler)
            assert reply.statusCode == 201, reply.json
            cls.handlers.append(reply.json['handler_id'])

            for img in events:
                reply = fsmRequests.emitEvent(
                    cls.handlers[handler_type],
                    img,
                    {
                        'user_data': cls.name,
                        'source': cls.name,
                        'tags': cls.name + ',' + cls.name + '1'
                    }
                )
                assert reply.statusCode == 201, reply.json
                cls.events.append(reply.json['events'][0])
        sleep(10)  # wait group ttl

        object_types = ('descriptors', 'persons', 'events', 'groups', 'events_attributes', 'groups_attributes')

        cross_matcher_tasks = [
            {
                "description": cls.name,
                "references": references,
                "candidates": {"list_id": list_id},
            }
            for references in [
                {
                    "objects": 'luna_list',
                    "filters": {"list_id": cls.outputListDescriptors},
                },
                {
                    "objects": 'luna_list',
                    "filters": {"list_id": cls.outputListPersons},
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handlers[0]]},
                },
                {
                    "objects": 'groups',
                    "filters": {"handler_ids": [cls.handlers[0]]},
                },
                {
                    "objects": 'events',
                    "filters": {"handler_ids": [cls.handlers[1]]},
                },
                {
                    "objects": 'groups',
                    "filters": {"handler_ids": [cls.handlers[1]]},
                },
            ]
            for list_id in (cls.listDescriptors, cls.listPersons)
        ]

        replies = [fsmRequests.createTaskCrossMatcher(task) for task in cross_matcher_tasks]
        for reply in replies:
            assert reply.statusCode == 202, reply.json
        cls.cross_match_task_ids = dict(zip(
            (
                x + '_to_' + y
                for x in object_types
                for y in object_types[:2]
            ),
            (reply.json['task_id'] for reply in replies)
        ))

        clusterizer_tasks = [
            {
                "description": cls.name,
                "objects": "luna_list",
                "filters": {
                    "list_id": list_id
                }
            }
            for list_id in (cls.outputListDescriptors, cls.outputListPersons)
        ] + [
            {
                "description": cls.name,
                "objects": objects,
                "filters": {
                    "handler_ids": [handler]
                }
            }
            for handler in cls.handlers
            for objects in ("events", "groups")
        ]

        replies = [fsmRequests.createTaskClusterization(task) for task in clusterizer_tasks]
        for reply in replies:
            assert reply.statusCode == 202, reply.json
        cls.clusterizer_task_ids = dict(zip(
            object_types,
            (reply.json['task_id'] for reply in replies)
        ))

        # create failed task
        reply = fsmRequests.createTaskClusterization(
            {"objects": "events", "filters": {"handler_ids": [str(uuid4())]}, "description": cls.name})
        assert reply.statusCode == 202, reply.json
        cls.fail_task_id = reply.json['task_id']

        # wait tasks ready
        cls.wait_tasks_ready([*cls.cross_match_task_ids.values(), *cls.clusterizer_task_ids.values(), cls.fail_task_id])

    def assertCSVReport(self, task_id, attributes_enabled=0):
        # todo add attributes check
        reply = fsmRequests.getReport(task_id)
        self.assertEqual(reply.status_code, 200, 'Wrong report status_code, json: "{}"'.format(reply.json))
        self.assertEqual(reply.headers['Content-Type'], 'application/zip', reply.json)
        with ZipFile(BytesIO(reply.content)) as zipfile:
            with zipfile.open('{}.csv'.format(task_id)) as CSVfile:
                # get photos
                text = CSVfile.read().decode()
                table = [line.split(',') for line in text.split('\n')]
                photoCols = [i for i in range(len(table[0])) if 'Photo Name' in table[0][i]]
                photos = [line[i] for line in table[1:] for i in range(len(line)) if i in photoCols]
                attributesCols = [i for i in range(len(table[0])) if 'Reference Age' in table[0][i] or 'Reference Gender' in table[0][i]]
                attributes = [line[i] for line in table[1:] for i in range(len(line)) if i in attributesCols]
            # assert all photos exists
            self.assertEqual(len(set(photos)) + 1, len(zipfile.filelist), "Wrong count of files in zipfile")
            for photo in photos:
                self.assertIn('portraits/{}'.format(photos[0]), [file.filename for file in zipfile.filelist],
                              'Portrait "{}" is not in filelist'.format(photo))
            for attr in attributes:
                if attributes_enabled:
                    self.assertTrue(attr.isdigit(), attributes)
                else:
                    self.assertEqual(attr, 'None', attributes)

    def assertPDFReport(self, task_id):
        reply = fsmRequests.getReport(task_id)
        self.assertEqual(reply.status_code, 200, 'Wrong report status_code, json: "{}"'.format(reply.json))
        self.assertEqual(reply.headers['Content-Type'], 'application/pdf', reply.json)

    def test_cross_match_descriptors_to_descriptors_csv(self):
        cross_match_task_id = self.cross_match_task_ids['descriptors_to_descriptors']
        reply = fsmRequests.createTaskReporter({"task_id": cross_match_task_id, "format": "csv", "parameters": {
            "save_portraits": 1
        }, "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        task_id = reply.json['task_id']
        self.wait_tasks_ready([task_id])
        self.assertCSVReport(task_id)

    def test_cross_match_descriptors_to_persons_csv(self):
        cross_match_task_id = self.cross_match_task_ids['descriptors_to_persons']
        reply = fsmRequests.createTaskReporter({"task_id": cross_match_task_id, "format": "csv", "parameters": {
            "save_portraits": 1
        }, "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        task_id = reply.json['task_id']
        self.wait_tasks_ready([task_id])
        self.assertCSVReport(task_id)

    def test_cross_match_persons_to_descriptors_csv(self):
        cross_match_task_id = self.cross_match_task_ids['persons_to_descriptors']
        reply = fsmRequests.createTaskReporter({"task_id": cross_match_task_id, "format": "csv", "parameters": {
            "save_portraits": 1
        }, "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        task_id = reply.json['task_id']
        self.wait_tasks_ready([task_id])
        self.assertCSVReport(task_id)

    def test_cross_match_persons_to_persons_csv(self):
        cross_match_task_id = self.cross_match_task_ids['persons_to_persons']
        reply = fsmRequests.createTaskReporter({"task_id": cross_match_task_id, "format": "csv", "parameters": {
            "save_portraits": 1
        }, "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        task_id = reply.json['task_id']
        self.wait_tasks_ready([task_id])
        self.assertCSVReport(task_id)

    def test_cross_match_events_to_descriptors_csv(self):
        for attributes in range(1, 2):
            task_name = {0: 'events_to_descriptors', 1: 'events_attributes_to_descriptors'}[attributes]
            with self.subTest(task_name):
                cross_match_task_id = self.cross_match_task_ids[task_name]
                reply = fsmRequests.createTaskReporter({"task_id": cross_match_task_id, "format": "csv", "parameters": {
                    "save_portraits": 1
                }, "description": self.name})
                self.assertEqual(202, reply.statusCode, reply.json)
                task_id = reply.json['task_id']
                self.wait_tasks_ready([task_id])
                self.assertCSVReport(task_id)

    def test_cross_match_events_to_persons_csv(self):
        for attributes in range(2):
            task_name = {0: 'events_to_persons', 1: 'events_attributes_to_persons'}[attributes]
            with self.subTest(task_name):
                cross_match_task_id = self.cross_match_task_ids[task_name]
                reply = fsmRequests.createTaskReporter({"task_id": cross_match_task_id, "format": "csv", "parameters": {
                    "save_portraits": 1
                }, "description": self.name})
                self.assertEqual(202, reply.statusCode, reply.json)
                task_id = reply.json['task_id']
                self.wait_tasks_ready([task_id])
                self.assertCSVReport(task_id)

    def test_cross_match_groups_to_descriptors_csv(self):
        for attributes in range(2):
            task_name = {0: 'groups_to_descriptors', 1: 'groups_attributes_to_descriptors'}[attributes]
            with self.subTest(task_name):
                cross_match_task_id = self.cross_match_task_ids[task_name]
                reply = fsmRequests.createTaskReporter({"task_id": cross_match_task_id, "format": "csv", "parameters": {
                    "save_portraits": 1
                }, "description": self.name})
                self.assertEqual(202, reply.statusCode, reply.json)
                task_id = reply.json['task_id']
                self.wait_tasks_ready([task_id])
                self.assertCSVReport(task_id)

    def test_cross_match_groups_to_persons_csv(self):
        for attributes in range(2):
            task_name = {0: 'groups_to_persons', 1: 'groups_attributes_to_persons'}[attributes]
            with self.subTest(task_name):
                cross_match_task_id = self.cross_match_task_ids[task_name]
                reply = fsmRequests.createTaskReporter({"task_id": cross_match_task_id, "format": "csv", "parameters": {
                    "save_portraits": 1
                }, "description": self.name})
                self.assertEqual(202, reply.statusCode, reply.json)
                task_id = reply.json['task_id']
                self.wait_tasks_ready([task_id])
                self.assertCSVReport(task_id)

    # todo @skipIf(not USE_LATEX, "Latex disabled")
    def test_cross_match_descriptors_to_descriptors_pdf(self):
        if not USE_LATEX:
            return
        cross_match_task_id = self.cross_match_task_ids['descriptors_to_descriptors']
        reply = fsmRequests.createTaskReporter({"task_id": cross_match_task_id, "format": "pdf", "parameters": {
            "colors_bounds": {"red": 0.8, "orange": 0.4, "green": 0.0}
        }, "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        task_id = reply.json['task_id']
        self.wait_tasks_ready([task_id])
        self.assertPDFReport(task_id)

    def test_clusterization_descriptors_csv(self):
        clusterization_task_id = self.clusterizer_task_ids['descriptors']
        reply = fsmRequests.createTaskReporter({"task_id": clusterization_task_id, "format": "csv", "parameters": {
            "save_portraits": 1
        }, "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        task_id = reply.json['task_id']
        self.wait_tasks_ready([task_id])
        self.assertCSVReport(task_id)

    def test_clusterization_persons_csv(self):
        clusterization_task_id = self.clusterizer_task_ids['persons']
        reply = fsmRequests.createTaskReporter({"task_id": clusterization_task_id, "format": "csv", "parameters": {
            "save_portraits": 1
        }, "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        task_id = reply.json['task_id']
        self.wait_tasks_ready([task_id])
        self.assertCSVReport(task_id)

    def test_clusterization_events_csv(self):
        for attributes in range(2):
            task_name = {0: 'events', 1: 'events_attributes'}[attributes]
            with self.subTest(task_name):
                clusterization_task_id = self.clusterizer_task_ids[task_name]
                reply = fsmRequests.createTaskReporter({"task_id": clusterization_task_id, "format": "csv", "parameters": {
                    "save_portraits": 1
                }, "description": self.name})
                self.assertEqual(202, reply.statusCode, reply.json)
                task_id = reply.json['task_id']
                self.wait_tasks_ready([task_id])
                self.assertCSVReport(task_id, attributes)

    def test_clusterization_groups_csv(self):
        for attributes in range(2):
            task_name = {0: 'groups', 1: 'groups_attributes'}[attributes]
            with self.subTest(task_name):
                clusterization_task_id = self.clusterizer_task_ids[task_name]
                reply = fsmRequests.createTaskReporter({"task_id": clusterization_task_id, "format": "csv", "parameters": {
                    "save_portraits": 1
                }, "description": self.name})
                self.assertEqual(202, reply.statusCode, reply.json)
                task_id = reply.json['task_id']
                self.wait_tasks_ready([task_id])
                self.assertCSVReport(task_id, attributes)

    # todo @skipIf(not USE_LATEX, "Latex disabled")
    def test_clusterization_descriptors_pdf(self):
        if not USE_LATEX:
            return
        clusterization_task_id = self.clusterizer_task_ids['descriptors']
        reply = fsmRequests.createTaskReporter({"task_id": clusterization_task_id, "format": "pdf", "parameters": {
            "colors_bounds": {"red": 0.8, "orange": 0.4, "green": .0}
        }, "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        task_id = reply.json['task_id']
        self.wait_tasks_ready([task_id])
        self.assertPDFReport(task_id)

    def test_nonexistent_task_id(self):
        primary_task_id = max(self.clusterizer_task_ids.values()) + 100
        reply = fsmRequests.createTaskReporter({"task_id": primary_task_id, "format": "csv", "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        secondary_task_id = reply.json['task_id']
        self.wait_tasks_ready([secondary_task_id])
        reply = fsmRequests.getDoneTask(secondary_task_id)
        self.assertEqual(reply.statusCode, 200, 'Wrong report status_code, json: "{}"'.format(reply.json))
        self.assertEqual(reply.json['result']['errors']['errors'][0],
                         {'error_code': 13010, 'detail': 'No task found by id'})

    def test_failed_task_id(self):
        primary_task_id = self.fail_task_id
        reply = fsmRequests.createTaskReporter({"task_id": primary_task_id, "format": "csv", "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        secondary_task_id = reply.json['task_id']
        self.wait_tasks_ready([secondary_task_id])
        reply = fsmRequests.getDoneTask(secondary_task_id)
        self.assertEqual(reply.statusCode, 200, 'Wrong report status_code, json: "{}"'.format(reply.json))
        self.assertEqual(reply.json['result']['errors']['errors'][0], {
            'detail': 'Inconsistent input data found: "Reporter got task {} with status \'failed\'"'.format(
                primary_task_id), 'error_code': 15007})

    def test_wrong_task_type(self):
        reply = fsmRequests.createTaskHitTopN({
            "list_id": self.listPersons,
            "top_n": 4,
            "description": self.name
        })
        primary_task_id = reply.json['task_id']
        self.wait_tasks_ready([primary_task_id])
        reply = fsmRequests.createTaskReporter({"task_id": primary_task_id, "format": "csv", "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        secondary_task_id = reply.json['task_id']
        self.wait_tasks_ready([secondary_task_id])
        reply = fsmRequests.getDoneTask(secondary_task_id)
        self.assertEqual(reply.statusCode, 200, 'Wrong report status_code, json: "{}"'.format(reply.json))
        self.assertEqual(reply.json['result']['errors']['errors'][0],
                         {'detail': 'Result generator is not implemented yet', 'error_code': 15006})

    def test_wrong_format(self):
        cross_match_task_id = self.cross_match_task_ids['descriptors_to_descriptors']
        reply = fsmRequests.createTaskReporter({"task_id": cross_match_task_id, "format": "jpeg", "parameters": {
            "save_portraits": 1
        }, "description": self.name})
        self.assertEqual(reply.statusCode, 400)
        self.assertEqual(reply.json, {
            'error_code': 12019,
            'detail': "Failed to validate input json. Path: 'format',  message: ''jpeg' is not one of ['pdf', 'csv']'"
        })

    # todo @skipIf(USE_LATEX, "Latex enabled")
    def test_forbidden_without_latex(self):
        if USE_LATEX:
            return
        reply = fsmRequests.createTaskReporter({"task_id": 777, "format": "pdf"})
        self.assertEqual(403, reply.statusCode, "Got wrong status code")
        self.assertDictEqual(
            {"error_code": 12025, "detail": "LaTeX is disabled according to the current configuration"},
            reply.json,
            "Wrong error description"
        )

    def test_additional_fields(self):
        perfect_task = {
            "task_id": 1011,
            "format": "pdf",
            "parameters": {
                "colors_bounds": {
                    "green": 0.1,
                    "orange": 0.2,
                    "red": 0.3
                }
            },
            "description": self.name
        }
        self.corrupt_test(perfect_task, ('', 'parameters', 'parameters.colors_bounds'), fsmRequests.createTaskReporter)

    def test_location(self):
        reply = fsmRequests.createTaskReporter({"task_id": self.clusterizer_task_ids['descriptors'], "format": "csv",
                                                "description": self.name})
        self.assertEqual(202, reply.statusCode, reply.json)
        task_id = reply.json['task_id']
        self.wait_tasks_ready([task_id])
        done_task = fsmRequests.getDoneTask(task_id)
        self.assertEqual('/api/{}/reports/{}'.format(FSM2_API_VERSION, task_id),
                         done_task.headers['Location'])
