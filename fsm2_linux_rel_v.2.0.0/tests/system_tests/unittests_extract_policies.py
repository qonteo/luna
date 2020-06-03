from tests.system_tests.base_test_handlers_logic import *
import unittest


class TestExtractPolicies(BaseTestsHandlersPolicies):
    handlers = {}

    @staticmethod
    def generateHandler(handlerType, name, extractPolicy=None):
        if handlerType == "extract":
            handlerSchema = {
                "name": "test_visionlabs_{}_{}".format(name, handlerType),
                "type": "extract",
                "multiple_faces_policy": 0
            }
        else:
            handlerSchema = {
                "name": "{}_{}".format(name, handlerType),
                "type": "search",

                "search_policy": {
                    "search_lists": [
                        {
                            "list_id": TestExtractPolicies.personsMatchingLists[0], "threshold": 0.11,
                            "list_type": "persons",
                            "limit": 1
                        }
                    ],
                    "search_priority": 1
                }
            }
        if extractPolicy is not None:
            handlerSchema["extract_policy"] = extractPolicy

        reply = createHandler(handlerSchema)
        handler = handlerSchema
        handler["id"] = reply.json["handler_id"]
        return handler

    def test_extract_policy_warped_image(self):
        for handlerType in ["extract", "search"]:
            with self.subTest(handlerType=handlerType, warped_image=1):
                handler = TestExtractPolicies.generateHandler(handlerType, "extract_policy_warped_image")
                reply = emitEvent(handler["id"], "./data/non_warped.jpg", queryParams={"warped_image": 1})
                self.assertEqual(reply.statusCode, 400, handlerType)
                self.assertTrue(validate(ERROR_SCHEMA, reply.json) is None, handlerType)
                self.assertTrue(reply.json["detail"].find("error_code: 3002") > 0,
                                handlerType)
            with self.subTest(handlerType=handlerType, warped_image=0):
                reply = emitEvent(handler["id"], "./data/non_warped.jpg", queryParams={"warped_image": 0})
                self.validateEvent(reply, handler)
                reply = emitEvent(handler["id"], "./data/non_warped.jpg", queryParams={})
                self.validateEvent(reply, handler)

    def test_extract_policy_estimate_quality(self):

        for estimateQuality in [0, 1]:
            with self.subTest(estimateQuality=estimateQuality):
                for handlerType in ["extract", "search"]:
                    with self.subTest(handlerType=handlerType, estimateQuality=estimateQuality):
                        handler = TestExtractPolicies.generateHandler(handlerType, "extract_policy_estimate_quality",
                                                                      extractPolicy={"estimate_quality":
                                                                                         estimateQuality})

                        reply = emitEvent(handler["id"], "./data/man_old.jpg", queryParams={"warped_image": 1})
                        self.assertEqual(reply.statusCode, 201, handlerType)
                        self.validateEvent(reply, handler)
                        if estimateQuality:
                            self.assertTrue("quality" in reply.json["events"][0]["extract"])
                        else:
                            self.assertTrue("quality" not in reply.json["events"][0]["extract"])

    def test_extract_policy_estimate_attributes(self):

        for estimateAttributes in [0, 1]:
            with self.subTest(estimateAttributes=estimateAttributes):
                for handlerType in ["extract", "search"]:
                    with self.subTest(handlerType=handlerType, estimateAttributes=estimateAttributes):
                        handler = TestExtractPolicies.generateHandler(handlerType, "extract_policy_estimate_attributes",
                                                                      extractPolicy={"estimate_attributes":
                                                                                         estimateAttributes})
                        reply = emitEvent(handler["id"], "./data/man_old.jpg", queryParams={"warped_image": 1})
                        self.assertEqual(reply.statusCode, 201, handlerType)
                        self.validateEvent(reply, handler)
                        if estimateAttributes:
                            self.assertTrue("attributes" in reply.json["events"][0]["extract"])
                        else:
                            self.assertTrue("attributes" not in reply.json["events"][0]["extract"])

    # todo @unittest.skip('receive wrong status code from api')
    def test_extract_policy_score_threshold(self):
        return
        for scoreThreshold in [0.99, 0.999]:
            with self.subTest(scoreThreshold=scoreThreshold):
                for handlerType in ["extract", "search"]:
                    with self.subTest(handlerType=handlerType):
                        handler = TestExtractPolicies.generateHandler(handlerType, "extract_policy_score_threshold",
                                                                      extractPolicy={"score_threshold":
                                                                                         scoreThreshold})
                        reply = emitEvent(handler["id"], "./data/man_old.jpg", queryParams={"warped_image": 1})
                        if scoreThreshold == 0.99:
                            self.assertEqual(reply.statusCode, 201, handlerType)
                            self.validateEvent(reply, handler)
                        else:
                            self.assertEqual(reply.statusCode, 400, handlerType)
                            self.assertTrue(validate(ERROR_SCHEMA, reply.json) is None, handlerType)
                            self.assertTrue(reply.json["detail"].find("error_code: 4010") > 0,
                                            handlerType)
