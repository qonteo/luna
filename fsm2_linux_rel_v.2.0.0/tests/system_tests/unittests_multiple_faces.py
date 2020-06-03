from tests.system_tests.base_test_handlers_logic import *
from tests.system_tests.handlers.multiple_face_policy_handler import MultipleFacePolicyHandler


class TestMultipleFacesPolicy(MultipleFacePolicyHandler):

    def test_handlers_multi_faces_error(self):
        for handler in self.create_search_handler():
            with self.subTest(handlerName=handler["name"]):
                reply = createHandler(handler)
                handlerId = reply.json["handler_id"]
                reply = emitEvent(handlerId, "./data/girl_and_man.jpg", queryParams={})
                self.assertEqual(reply.statusCode, 400, handler["name"])
                self.assertTrue(validate(reply.json, MULTI_FACE_FSM_ERROR) is None, handler["name"])

    def test_handlers_multi_faces_true(self):
        reply = createHandler(self.create_multiple_face_true_handler())
        handlerId = reply.json["handler_id"]
        reply = emitEvent(handlerId, "./data/girl_and_man.jpg", queryParams={})
        self.assertEqual(reply.statusCode, 201, self.create_multiple_face_true_handler()["name"])
        self.assertTrue(validate(reply.json, EXTRACT_EVENT_SCHEMA) is None, self.create_multiple_face_true_handler()["name"])

    def test_handlers_multi_faces_descriptor_simple_policy(self):

        def test(testData, handlerForTest):
            eventReply = emitEvent(handlerForTest["id"], testData["img"], queryParams={"warped_image": 1})
            self.validateEvent(eventReply, handlerForTest,
                               descriptorsLists=[TestMultipleFacesPolicy.descriptorsAttachLists[0]])

        descriptorPolicy = {
            "attach_policy": [{"list_id": TestMultipleFacesPolicy.descriptorsAttachLists[0]}]
        }

        for handlerType in ["extract", "search"]:
            handler = createTestHandler(handlerType, name="simple_descriptor_policy",
                                        descriptorPolicy=descriptorPolicy)

            data = {
                "img": "./data/girl_1_0.jpg",
                "list_id": TestMultipleFacesPolicy.personsMatchingLists[1]
            }
            test(data, handler)

    def test_handlers_multi_faces_descriptor_policy_with_one_filter(self):
        handler = self.creater_multiple_faces_handler()
        reply = emitEvent(handler[1]["id"], handler[0]["img"])
        for event in reply.json["events"]:
            if event["extract"]["attributes"]["gender"] > 0.5:
                self.checkEvent(event, handler[1], descriptorLists=handler[0]["gender_list"])
            else:
                self.checkEvent(event, handler[1], descriptorLists=handler[0]["age_list"])
