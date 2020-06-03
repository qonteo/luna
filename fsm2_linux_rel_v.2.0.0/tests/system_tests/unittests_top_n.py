from tests.system_tests.base_test_class import BaseTest, skipWithIncrementCount
import time
from tests.system_tests.fsmRequests import *
from tests.system_tests.shemas import *
from jsonschema import validate
import uuid

personsImgs = [["./data/girl_{}_{}.jpg".format(i, j) for j in range(3)] for i in range(1, 3)]
personsImgs.append(["./data/man_1_{}.jpg".format(j) for j in range(3)])
personsImgs.append(["./data/group_1_{}.jpg".format(j) for j in range(3)])
personsImgs.append(["./data/girl_young.jpg", "./data/man_young.jpg", "./data/girl_old.jpg"])


class TestsHitTopN(BaseTest):
    name = 'test_visionlabs_hit_top_n'
    personsList = None
    persons = []

    @classmethod
    def setUpClass(cls):
        TestsHitTopN.personsList = \
            TestsHitTopN.lunaClient.createList("persons", "test_fsm_visionlabs_top_n", raiseError=True).body[
                "list_id"]

        TestsHitTopN.persons = [
            TestsHitTopN.lunaClient.createPerson("test_fsm_person_top_hit_{}".format(i)).body["person_id"]
            for i in range(len(personsImgs))]
        for count, personImgs in enumerate(personsImgs):
            descriptors = [
                TestsHitTopN.lunaClient.extractDescriptors(filename=img, warpedImage=True, raiseError=True).body[
                    "faces"][0]["id"] for img in personImgs]
            for descriptor in descriptors:
                TestsHitTopN.lunaClient.linkDescriptorToPerson(TestsHitTopN.persons[count], descriptor,
                                                               raiseError=True)
            TestsHitTopN.lunaClient.linkListToPerson(TestsHitTopN.persons[count], TestsHitTopN.personsList,
                                                     raiseError=True)

    def test_hit_top_n(self):
        payload = {"list_id": TestsHitTopN.personsList, "top_n": 4, "description": self.name}
        reply = createTaskHitTopN(payload)
        self.assertTrue("task_id" in reply.json, reply.json)
        taskId = reply.json["task_id"]
        reply = getDoneTask(taskId)
        self.assertEqual(404, reply.statusCode)
        reply = getTaskInProgress(taskId)
        self.assertEqual(200, reply.statusCode)
        self.wait_tasks_ready([taskId])
        reply = getDoneTask(taskId)
        self.assertEqual(200, reply.statusCode)
        self.assertTrue(validate(reply.json, TASK_HIT_TOP_N_SCHEMA) is None, reply.json)
        self.assertTrue(reply.json["result"]["success"]['total'] == len(reply.json["result"]["success"]['tops']) == 4)
        self.assertTrue(reply.json["result"]["success"]['tops'][0] < 0.9)
        for i in range(reply.json["result"]["success"]['total'] - 1):
            self.assertTrue(reply.json["result"]["success"]['tops'][i] <=
                            reply.json["result"]["success"]['tops'][i + 1])

    def test_hit_top_n_param_n(self):

        mapTopTasks = {}
        for i in range(1, 7):
            payload = {"list_id": TestsHitTopN.personsList, "top_n": i, "description": self.name}
            reply = createTaskHitTopN(payload)
            self.assertEqual(reply.statusCode, 202, reply.json)
            taskId = reply.json["task_id"]
            mapTopTasks[i] = taskId

        self.wait_tasks_ready(mapTopTasks.values())

        time.sleep(5)
        for top, taskId in mapTopTasks.items():
            with self.subTest(top=top):
                reply = getDoneTask(taskId)
                self.assertTrue(validate(reply.json, TASK_HIT_TOP_N_SCHEMA) is None, reply.json)
                self.assertTrue(
                    reply.json["result"]["success"]['total'] == len(reply.json["result"]["success"]['tops']) == top
                )
                self.assertTrue(reply.json["result"]["success"]['tops'][0] < 0.9)
                for j in range(reply.json["result"]["success"]['total'] - 1):
                    self.assertTrue(reply.json["result"]["success"]['tops'][j] <=
                                    reply.json["result"]["success"]['tops'][j + 1])

                if top in (5, 6):
                    for j in range(4, reply.json["result"]["success"]['total'] - 1):
                        self.assertTrue(reply.json["result"]["success"]['tops'][j] ==
                                        reply.json["result"]["success"]['tops'][j + 1])

    def test_hit_top_n_fake_list(self):

        payload = {"list_id": str(uuid.uuid4()), "top_n": 4, "description": self.name}
        reply = createTaskHitTopN(payload)
        self.assertEqual(reply.statusCode, 202, reply.json)
        taskId = reply.json["task_id"]
        time.sleep(3)
        reply = getDoneTask(taskId)
        self.assertEqual(200, reply.statusCode)
        self.assertTrue(validate(reply.json, TASK_SCHEMA) is None, reply.json)
        self.assertTrue("success" not in reply.json["result"], reply.json)
        self.assertEqual(reply.json["result"]["errors"]["total"], 1, reply.json)
        self.assertEqual(reply.json["result"]["errors"]["errors"][0], {'error_code': 11007,
                                                                       'detail': 'get list request failed.  '
                                                                                 'error_code: 22003, detail: '
                                                                                 'List not found'},
                         reply.json)
        reply = getTaskInProgress(taskId)
        self.assertEqual(reply.statusCode, 303, reply.json)

    def test_hit_top_n_wrong_n(self):
        payload = {"list_id": str(uuid.uuid4()), "top_n": 0, "description": self.name}
        reply = createTaskHitTopN(payload)
        self.assertTrue(validate(reply.json, ERROR_SCHEMA) is None, reply.json)
        self.assertEqual(reply.json, {'error_code': 12019,
                                      'detail': "Failed to validate input json. Path: 'top_n',  message: '0 is less "
                                                "than the minimum of 1'"},
                         reply.json)

    @skipWithIncrementCount("for this tests need big list")
    def test_hit_top_n_cancelled(self):
        payload = {"list_id": TestsHitTopN.personsList, "top_n": 4, "description": self.name}
        taskId = createTaskHitTopN(payload).json["task_id"]
        reply = cancelTaskInProgress(taskId)
        self.assertEqual(reply.statusCode, 204, reply.json)
        time.sleep(3)
        reply = getDoneTask(taskId)
        self.assertTrue(validate(reply.json, TASK_SCHEMA) is None, reply.json)
        self.assertEqual(reply.json["status"], "cancelled", reply.json)
        reply = getTaskInProgress(taskId)
        self.assertEqual(reply.statusCode, 303, reply.json)

    def test_hit_top_n_additional_fields(self):
        perfect_task = {
            "list_id": "b3ed1366-e6b5-4a63-9b4c-25ccfb07f310",
            "top_n": 4,
            "description": "bad guys"
        }

        self.corrupt_test(perfect_task, ('',), createTaskHitTopN)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.deleteLunaAPIPersons(TestsHitTopN.persons)
        cls.deleteLunaAPILists([TestsHitTopN.personsList])
