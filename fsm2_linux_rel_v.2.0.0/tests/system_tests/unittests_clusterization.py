from uuid import uuid4

from tests.system_tests.base_test_class import BaseTest
from tests.system_tests.fsmRequests import *
from tests.system_tests.utils.work_with_storage import *
from datetime import datetime
import time
import copy


class EventStorage:
    def __init__(self, pathToImage, clusterId, handler):
        self.clusterId = clusterId
        self.descriptor = None
        self.person = None
        self.age = None
        self.gender = None
        self.img = pathToImage
        self.startUploadTime = None
        self.externalId = None
        self.handlerId = handler
        self.groupId = None
        self.id = None
        self.source = None
        self.tags = None

    def uploadImage(self, externalId, source, userData="", tags=None):
        self.externalId = externalId
        queryParams = {"external_id": self.externalId, "warped_img": 1, "source": source,
                       "user_data": userData}
        if tags is not None:
            queryParams["tags"] = ",".join(tags)
        event = emitEvent(self.handlerId, self.img, queryParams)
        self.startUploadTime = datetime.strptime(event.json["events"][0]["create_time"], '%Y-%m-%dT%H:%M:%SZ')
        self.age = event.json["events"][0]["extract"]["attributes"]["age"]
        self.gender = event.json["events"][0]["extract"]["attributes"]["gender"]
        self.descriptor = event.json["events"][0]["id"]
        self.person = event.json["events"][0]["person_id"]
        self.groupId = event.json["events"][0]["group_id"]
        self.source = source
        self.id = self.descriptor
        self.tags = tags if tags is not None else []

    def isSuitable(self, filters):
        for objectFilter in filters:
            if not objectFilter.comp(self.__dict__[filters.attribute]):
                return False
        return True


class GroupStorage:
    def __init__(self, events):
        self.age = sum([event.age for event in events]) / float(len(events))
        self.gender = sum([event.gender for event in events]) / float(len(events))
        self.tags = list(set().union(*[event.tags for event in events]))
        self.source = events[0].source
        self.groupId = events[0].groupId
        self.id = self.groupId
        self.handlerId = events[0].handlerId
        self.createTime = min([event.startUploadTime for event in events])
        self.clusterId = events[0].clusterId if events[0].clusterId != 2 else 1

    def isSuitable(self, filters):
        for objectFilter in filters:
            if not objectFilter.comp(self.__dict__[filters.attribute]):
                return False
        return True


class TestsClusterization(BaseTest):
    personsList = None
    descriptorList = None
    descriptors = []
    persons = []
    handlerId = None
    events = []
    trashEvent = None
    trashGroup = None
    groups = []
    startUploadEvents = None
    endUploadEvents = None

    @classmethod
    def setUpClass(cls):
        cls.startUploadEvents = datetime.now().isoformat('T').split('.')[0] + 'Z'

        TestsClusterization.descriptorList = TestsClusterization.lunaClient.createList(
            "descriptors", "test_visionlabs_clusterization_descriptors_list", True).body["list_id"]
        TestsClusterization.personsList = TestsClusterization.lunaClient.createList(
            "persons", "test_visionlabs_clusterization_descriptors_list", True).body["list_id"]

        handler = {
            "name": "test_visionlabs_clusterization",
            "type": "extract",
            "multiple_faces_policy": 0,
            "extract_policy": {
                "estimate_attributes": 1
            },
            "descriptor_policy": {
                "attach_policy": [{"list_id": TestsClusterization.descriptorList}]
            },
            "person_policy": {"create_person_policy": {
                "create_person": 1,
                "attach_policy": [{"list_id": TestsClusterization.personsList}]
            }
            },
            "grouping_policy":
                {
                    "ttl": 10,
                    "grouper": 1,
                    "threshold": 0.6
                }
        }

        handlerTrash = {
            "name": "test_visionlabs_clusterization",
            "type": "extract",
            "multiple_faces_policy": 0,
            "extract_policy": {
                "estimate_attributes": 1
            },
            "grouping_policy":
                {
                    "ttl": 10,
                    "grouper": 1,
                    "threshold": 0.6
                }
        }

        handlerId = TestsClusterization.handlerId = createHandler(handler).json["handler_id"]
        handlerTrashId = createHandler(handlerTrash).json["handler_id"]

        person1 = [{"img": "./data/girl_1_{}.jpg".format(i),
                    "tags": ["beer"],
                    "source": "cam1",
                    "externalId": 1,
                    "userData": "test_visionlabs_clusterization " + "girl_1_{}.jpg".format(i)} for i in range(3)]

        person2 = [{"img": "./data/girl_2_{}.jpg".format(i),
                    "tags": ["beer", "vodka"],
                    "source": "cam1",
                    "externalId": 1 if i == 0 else 2,
                    "userData": "test_visionlabs_clusterization " + "girl_2_{}.jpg".format(i)} for i in range(3)]

        person3 = [{"img": "./data/man_1_{}.jpg".format(i),
                    "tags": ["vodka"],
                    "source": "cam1",
                    "externalId": 3,
                    "userData": "test_visionlabs_clusterization " + "man_1_{}.jpg".format(i)} for i in range(3)]

        person4 = [{"img": "./data/group_1_{}.jpg".format(i),
                    "tags": None,
                    "source": "cam2",
                    "externalId": 3,
                    "userData": "test_visionlabs_clusterization " + "group_1_{}.jpg".format(i)} for i in range(3)]

        person5 = [{"img": "./data/girl_young.jpg",
                    "tags": None,
                    "source": "cam3",
                    "externalId": 3,
                    "userData": "test_visionlabs_clusterization " + "trash"}]

        for count, person in enumerate([person1, person2, person3, person4]):
            for ev in person:
                event = EventStorage(ev["img"], count + 1, handlerId)
                event.uploadImage(ev["externalId"], ev["source"], ev["userData"], ev["tags"])
                TestsClusterization.events.append(event)

        groups = {}
        for event in TestsClusterization.events:
            if event.groupId in groups:
                groups[event.groupId].append(event)
            else:
                groups[event.groupId] = [event]

        for group, events in groups.items():
            TestsClusterization.groups.append(GroupStorage(events))

        for ev in person5:
            event = EventStorage(ev["img"], 5, handlerTrashId)
            event.uploadImage(ev["externalId"], ev["source"], ev["userData"], ev["tags"])
            TestsClusterization.trashEvent = event
        TestsClusterization.trashGroup = GroupStorage([TestsClusterization.trashEvent])

        time.sleep(1)
        cls.endUploadEvents = datetime.now().isoformat('T').split('.')[0] + 'Z'

    @staticmethod
    def getExpectedClusters(filters, typeObjects):
        expectedClusters = {}

        if typeObjects == "events":
            events = TestsClusterization.events + [TestsClusterization.trashEvent]
            expectedObjects = []
            for event in events:
                for evetsFilter in filters:
                    if not evetsFilter(event):
                        break
                else:
                    expectedObjects.append(event)
            for event in expectedObjects:
                if event.clusterId in expectedClusters:
                    expectedClusters[event.clusterId].append(event)
                else:
                    expectedClusters[event.clusterId] = [event]

            return [clusters for clusterId, clusters in expectedClusters.items()]
        elif typeObjects == "groups":
            groups = TestsClusterization.groups + [TestsClusterization.trashGroup]
            expectedObjects = []
            for group in groups:
                for groupsFilter in filters:
                    if not groupsFilter(group):
                        break
                else:
                    expectedObjects.append(group)
            for group in expectedObjects:
                if group.clusterId in expectedClusters:
                    expectedClusters[group.clusterId].append(group)
                else:
                    expectedClusters[group.clusterId] = [group]

            return [clusters for clusterId, clusters in expectedClusters.items()]

    @classmethod
    def initFilters(cls):
        # todo implement moar filters
        filterAge = {
            "name": "age",
            "filters":
                {
                    "create_time__lt": cls.endUploadEvents,
                    "create_time__gt": cls.startUploadEvents,
                    "age__gt": 24,
                    "age__lt": 45,
                },
            "comparator": lambda event: 24 <= event.age <= 45
        }
        filterGender = {
            "name": "gender",
            "filters":
                {
                    "create_time__lt": cls.endUploadEvents,
                    "create_time__gt": cls.startUploadEvents,
                    "gender": 0,
                },
            "comparator": lambda event: event.gender <= 0.5
        }

        filterSource = {
            "name": "source",
            "filters":
                {
                    "create_time__lt": cls.endUploadEvents,
                    "create_time__gt": cls.startUploadEvents,
                    "sources": ["cam1", "cam2"],
                },
            "comparator": lambda event: event.source in ["cam1", "cam2"]
        }

        filterTags = {
            "name": "tags",
            "filters":
                {
                    "create_time__lt": cls.endUploadEvents,
                    "create_time__gt": cls.startUploadEvents,
                    "tags": ["beer", "vodka"],
                },
            "comparator": lambda event: len(set(event.tags).intersection(["beer", "vodka"])) == len(["beer", "vodka"])
        }

        filterHandler = {
            "name": "handler",
            "filters":
                {
                    "create_time__lt": cls.endUploadEvents,
                    "create_time__gt": cls.startUploadEvents,
                    "handler_ids": [TestsClusterization.handlerId],
                },
            "comparator": lambda event: event.handlerId == cls.handlerId
        }

        setFilters = [filterHandler, filterTags, filterSource, filterGender, filterAge]
        return setFilters

    def checkClusters(self, clusters, expectedClusters, attr="id"):

        self.assertEqual(len(clusters), len(expectedClusters))
        for cluster in expectedClusters:
            firstElement = cluster[0]
            for inputCluster in clusters:
                clustersRaw = [element["id"] for element in inputCluster]
                if firstElement.__dict__[attr] in set(clustersRaw):
                    self.assertSetEqual(set(clustersRaw), set([element.__dict__[attr] for element in cluster]))
                    break
            else:
                self.fail("cluster for object not found")

    def test_clusterization_by_descriptors_list(self):

        task = {
            "description": "test_visionlabs_clusterization_by_descriptors_list",
            "objects": "luna_list",
            "filters":
                {
                    "list_id": TestsClusterization.descriptorList

                }
        }
        done_task = self.complete_clusterization_task(task)

        expectedClusters = self.getExpectedClusters([lambda event: event.handlerId == TestsClusterization.handlerId],
                                                    "events")
        self.checkClusters(done_task["result"]["success"]["clusters"], expectedClusters)

    def test_clusterization_by_non_exist_list(self):

        task = {
            "description": "test_visionlabs_clusterization_by_non_exist_list",
            "objects": "luna_list",
            "filters":
                {
                    "list_id": '11111111-1111-4a11-8111-111111111111'

                }
        }
        done_task = self.complete_clusterization_task(task)

        error = done_task["result"]["errors"]["errors"][0]
        self.assertEqual(11007, error["error_code"])
        self.assertEqual("get list '11111111-1111-4a11-8111-111111111111' request failed.  error_code: 22003, "
                         "detail: List not found", error["detail"])

    def test_clusterization_by_persons_list(self):
        task = {
            "description": "test_visionlabs_clusterization_by_persobs_list",
            "objects": "luna_list",
            "filters":
                {
                    "list_id": TestsClusterization.personsList

                }
        }
        done_task = self.complete_clusterization_task(task)

        expectedClusters = self.getExpectedClusters([lambda event: event.handlerId == TestsClusterization.handlerId],
                                                    "events")
        self.checkClusters(done_task["result"]["success"]["clusters"], expectedClusters, "person")

    def test_clusterization_by_events(self):

        task = {
            "description": "test_visionlabs_clusterization_by_events",
            "objects": "events",
            "filters":
                {
                    "create_time__lt": TestsClusterization.endUploadEvents,
                    "create_time__gt": TestsClusterization.startUploadEvents

                }
        }
        done_task = self.complete_clusterization_task(task)
        expectedClusters = self.getExpectedClusters([], "events")
        self.checkClusters(done_task["result"]["success"]["clusters"], expectedClusters)

    def test_clusterization_by_groups(self):

        task = {
            "description": "test_visionlabs_clusterization_by_events",
            "objects": "groups",
            "filters":
                {
                    "create_time__lt": TestsClusterization.endUploadEvents,
                    "create_time__gt": TestsClusterization.startUploadEvents

                }
        }
        done_task = self.complete_clusterization_task(task)
        expectedClusters = self.getExpectedClusters([], "groups")
        self.checkClusters(done_task["result"]["success"]["clusters"], expectedClusters)

    def test_clusterization_with_filters(self):

        for objectType in ["events", "groups"]:
            with self.subTest(objectType=objectType):

                setFilters = copy.deepcopy(TestsClusterization.initFilters())

                for objectFilter in setFilters:
                    with self.subTest(filterNam=objectFilter["name"]):
                        task = {
                            "description": "test_visionlabs_clusterization_by_{}_with_filters_{}".format(
                                objectType, objectFilter["name"]),
                            "objects": objectType,
                            "filters": objectFilter["filters"]
                        }
                        reply = createTaskClusterization(task)
                        self.assertEqual(reply.statusCode, 202, reply.json)
                        taskId = reply.json["task_id"]
                        objectFilter["task_id"] = taskId
                time.sleep(15)

                for objectFilter in setFilters:
                    with self.subTest(filterNam=objectFilter["name"]):
                        taskId = objectFilter["task_id"]
                        reply = getDoneTask(taskId)
                        self.assertEqual(200, reply.statusCode)
                        expectedClusters = self.getExpectedClusters([objectFilter["comparator"]], objectType)
                        self.checkClusters(reply.json["result"]["success"]["clusters"], expectedClusters)

    def test_clusterization_list_without_listId(self):
        task = {
            "description": "test_visionlabs_clusterization_by_descriptors_list",
            "objects": "luna_list",
            "filters":
                {

                }
        }
        reply = createTaskClusterization(task)
        self.assertEqual(reply.statusCode, 400)
        self.assertEqual(12019, reply.json["error_code"])
        self.assertEqual("Failed to validate input json. Path: 'filters',  message: ''list_id' is a required property'",
                         reply.json["detail"])

    def test_clusterization_filters_without_filters(self):
        for objectType in ["events", "groups"]:
            with self.subTest(objectType=objectType):
                task = {
                    "description": "test_visionlabs_clusterization_filters_without_filters",
                    "objects": objectType,
                    "filters":
                        {
                            "list_id": TestsClusterization.descriptorList
                        }
                }
                reply = createTaskClusterization(task)
                self.assertEqual(reply.statusCode, 400)
                self.assertEqual(12019, reply.json["error_code"])
                self.assertEqual("Failed to validate input json. Path: 'filters',  message: 'Additional properties are "
                                 "not allowed ('list_id' was unexpected)'",
                                 reply.json["detail"])

    def test_clusterization_bad_object(self):
        task = {
            "description": "test_visionlabs_clusterization_filters_without_filters",
            "objects": "objects",
            "filters":
                {
                    "list_id": TestsClusterization.descriptorList
                }
        }
        reply = createTaskClusterization(task)
        self.assertEqual(reply.statusCode, 400)
        self.assertEqual(12019, reply.json["error_code"])
        self.assertEqual("Failed to validate input json. Path: 'objects',  message: 'field 'objects' must be one of: "
                         "'luna_list', 'events', 'groups''", reply.json["detail"])

    def test_clusterization_without_object(self):
        task = {
            "description": "test_visionlabs_clusterization_filters_without_filters",
            "filters":
                {
                    "list_id": TestsClusterization.descriptorList
                }
        }
        reply = createTaskClusterization(task)
        self.assertEqual(reply.statusCode, 400)
        self.assertEqual(12003, reply.json["error_code"])
        self.assertEqual("Field 'objects' not found in json", reply.json["detail"])

    def test_clusterization_additional_fields(self):
        perfect_task = {
            "description": "test_visionlabs_clusterization_additional_fields_in_json",
            "objects": "luna_list",
            "filters":
                {
                    "list_id": TestsClusterization.descriptorList,
                }
        }
        self.corrupt_test(perfect_task, ('', 'filters'), createTaskClusterization)

    def complete_clusterization_task(self, task):
        reply = createTaskClusterization(task)
        self.assertEqual(reply.statusCode, 202, reply.json)
        taskId = reply.json["task_id"]
        reply = getDoneTask(taskId)
        self.assertEqual(404, reply.statusCode)
        reply = getTaskInProgress(taskId)
        self.assertEqual(200, reply.statusCode)
        self.wait_tasks_ready([taskId])
        reply = getDoneTask(taskId)
        self.assertEqual(200, reply.statusCode)
        return reply.json

    def test_clusterization_threshold_0(self):
        for objects in ('events', 'groups'):
            with self.subTest(objects=objects):
                task = {
                    "description": "test_visionlabs_clusterization_threshold_0",
                    "objects": objects,
                    "filters":
                        {
                            "create_time__lt": TestsClusterization.endUploadEvents,
                            "create_time__gt": TestsClusterization.startUploadEvents

                        },
                    "threshold": 0.0
                }
                done_task = self.complete_clusterization_task(task)
                self.assertEqual(1, done_task['result']['success']['total_clusters'], done_task)

    def test_clusterization_threshold_1(self):
        for objects in ('events', 'groups'):
            with self.subTest(objects=objects):
                task = {
                    "description": "test_visionlabs_clusterization_threshold_1",
                    "objects": objects,
                    "filters":
                        {
                            "create_time__lt": TestsClusterization.endUploadEvents,
                            "create_time__gt": TestsClusterization.startUploadEvents,
                            "handler_ids": [TestsClusterization.handlerId],

                        },
                    "threshold": 1.0
                }
                done_task = self.complete_clusterization_task(task)
                if objects == 'events':
                    self.assertEqual(
                        len(self.events),
                        done_task['result']['success']['total_clusters'],
                        done_task
                    )
                else:
                    self.assertEqual(
                        len(self.groups),
                        done_task['result']['success']['total_clusters'],
                        done_task
                    )

    def test_clusterization_threshold_01(self):
        for objects in ('events', 'groups'):
            with self.subTest(objects=objects):
                task = {
                    "description": "test_visionlabs_clusterization_threshold_003",
                    "objects": objects,
                    "filters":
                        {
                            "create_time__lt": TestsClusterization.endUploadEvents,
                            "create_time__gt": TestsClusterization.startUploadEvents,
                            "handler_ids": [TestsClusterization.handlerId],
                        },
                    "threshold": 0.1
                }
                done_task = self.complete_clusterization_task(task)
                if objects == 'events':
                    self.assertTrue(
                        done_task['result']['success']['total_objects'] >
                        done_task['result']['success']['total_clusters'] > 1,
                        done_task
                    )
                else:
                    self.assertTrue(
                        # count of groups
                        5 >
                        done_task['result']['success']['total_clusters'] > 1,
                        done_task['result']['success']['total_clusters']
                    )

    def test_clusterization_no_objects(self):
        for objects in ('events', 'groups'):
            with self.subTest(objects=objects):
                task = {
                    "description": "test_clusterization_no_objects",
                    "objects": objects,
                    "filters":
                        {
                            "handler_ids": [str(uuid4())],
                        },
                }
                failed_task = self.complete_clusterization_task(task)
                self.assertIn('errors', failed_task['result'], failed_task)
                self.assertTrue(1 == len(failed_task['result']['errors']['errors']) == \
                                failed_task['result']['errors']['total'], failed_task)
                self.assertEqual(failed_task['result']['errors']['errors'][0],
                                 {'detail': 'No objects for task found', 'error_code': 15008}, failed_task)
