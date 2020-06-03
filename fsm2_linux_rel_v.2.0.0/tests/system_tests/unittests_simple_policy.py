from tests.system_tests.base_test_handlers_logic import BaseTestsHandlersPolicies, SEARCH_EVENT_SCHEMA, validate
from tests.system_tests.handlers.simple_policy_handler import SimplePolicyHandler
import uuid
from tests.system_tests.fsmRequests import createHandler, emitEvent
from tests.system_tests.shemas import EVENT_SCHEMA


class TestSimplePolicy(SimplePolicyHandler):

    def test_handlers_simple_handler(self):
        """
        .. test:: test_handlers_simple_handler
            :resources: "/handlers"
            :description: test handlers simple handler
        """
        for handler in self.create_handlers_simple_handler(TestSimplePolicy.personsMatchingLists[0]):
            reply = createHandler(handler)
            handler_id = reply.json["handler_id"]
            reply = emitEvent(handler_id, "./data/girl_2_0.jpg", queryParams = {"warped_image": 1})
            self.assertEqual(reply.statusCode, 201, handler["name"])
            if handler["type"] == "search":
                self.assertTrue(validate(reply.json, SEARCH_EVENT_SCHEMA) is None, handler["name"])
            else:
                self.assertTrue(validate(reply.json, EVENT_SCHEMA) is None, handler["name"])
            self.checkEvent(reply.json["events"][0], handler)

    def test_non_exist_handler(self):
        reply = emitEvent(str(uuid.uuid4()), "./data/man_old.jpg")
        self.assertEqual(reply.statusCode, 404)
        self.assertEqual(reply.json["error_code"], 13003)

    def test_image_without_face(self):
        handlers = self.create_handlers_simple_handler(BaseTestsHandlersPolicies.personsMatchingLists[0])
        for handler in handlers:
            with self.subTest(handlerType=handler["type"]):
                reply = createHandler(handler)
                handler_id = reply.json["handler_id"]
                reply = emitEvent(handler_id, "./data/no_face.jpg", queryParams = {"warped_image": 0})
                self.assertEqual(reply.statusCode, 500, handler["name"])
                self.assertEqual(reply.json["error_code"], 11007)


    def test_attach_to_non_exist_lists(self):
        handlers = [self.create_extract_handler_non_exitst_personlist(),
                    self.create_extract_handler_non_exist_descriptor_list()
                    ]
        for handler in handlers:
            with self.subTest(handler=handler):
                reply = createHandler(handler)
                handler_id = reply.json["handler_id"]
                reply = emitEvent(handler_id, "./data/man_old.jpg", queryParams={"warped_image": 1})
                self.assertErrorCode(reply, handler)

    @classmethod
    def tearDownClass(cls):
        super(TestSimplePolicy, cls).tearDownClass()
        cls.deleteLunaAPILists(
            TestSimplePolicy.personsMatchingLists + TestSimplePolicy.descriptorsMatchingLists +
            TestSimplePolicy.personsAttachLists + TestSimplePolicy.descriptorsAttachLists + TestSimplePolicy.tempList)
