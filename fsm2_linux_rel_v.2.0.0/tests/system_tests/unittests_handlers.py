import time

from tests.system_tests.base_test_class import skipWithIncrementCount
from tests.system_tests.fsmRequests import createHandler, getHandlerById, getHandlers, putHandler
from tests.system_tests.handlers_examples import *
from tests.system_tests.handlers.simple_policy_handler import *
from tests.system_tests.shemas import CREATE_HANDLER_SCHEMAS, ERROR_SCHEMA
from tests.system_tests.test_data_option import additional_fields
from tests.system_tests.utils.work_with_handlers import *


class TestHandlersAPI(SimplePolicyHandler):
    @staticmethod
    def compareHandlerJsons(handlerJsonA, handlerJsonB):

        handlerJsonA_ = {k: v for k, v in handlerJsonA.items() if v is not None}
        handlerJsonB_ = {k: v for k, v in handlerJsonB.items() if v is not None}
        return compareDict(handlerJsonA_, handlerJsonB_)

    def test_create_and_get_simple_handlers(self):
        for handler in self.create_and_get_simple_handlers():
            reply = createHandler(handler)
            self.assertEqual(reply.statusCode, 201, handler["name"])
            self.assertTrue(validate(reply.json, CREATE_HANDLER_SCHEMAS) is None, handler["name"])
            savingHandlerJson = getHandlerById(reply.json["handler_id"])
            handler["id"] = reply.json["handler_id"]
            self.assertTrue(TestHandlersAPI.compareHandlerJsons(generateHandlerWithDefault(handler),
                                                                savingHandlerJson.json), handler["name"])

    def test_create_and_get_search_several_policies(self):

        handlers = [searchHandlerDescriptorPolicy, searchHandlerPersonPolicy, searchHandlerGroupPolicy,
                    searchHandlerGroupDescriptorPolicy, searchHandlerPersonDescriptorPolicy]
        for handler in handlers:
            with self.subTest(handler=handler["name"]):
                reply = createHandler(handler)
                self.assertEqual(reply.statusCode, 201, handler["name"])
                self.assertTrue(validate(reply.json, CREATE_HANDLER_SCHEMAS) is None, handler["name"])
                savinghandler = getHandlerById(reply.json["handler_id"])
                handler["id"] = reply.json["handler_id"]
                self.assertTrue(
                    TestHandlersAPI.compareHandlerJsons(generateHandlerWithDefault(handler), savinghandler.json),
                    handler["name"])

    def test_incompatible_create_person_policies(self):
        handler = searchHandlerIncompatibleGroupPersonPolicy
        reply = createHandler(handler)
        self.assertEqual(reply.statusCode, 400, handler["name"])
        self.assertTrue(validate(reply.json, ERROR_SCHEMA) is None, handler["name"])

    def test_incompatible_filters_policies(self):
        handlers = (searchHandlerIncompatibleFiltersPolicy, extractHandlerIncompatibleFiltersPolicy)
        for handler in handlers:
            reply = createHandler(handler)
            self.assertEqual(reply.statusCode, 400, handler["name"])
            self.assertTrue(validate(reply.json, ERROR_SCHEMA) is None, handler["name"])

    def test_requires_parameters(self):
        handlers = [
            handlerWithoutType, extractHandlerWithoutMultipleFacesPolicy, searchHandlerWithoutSearchPolicy,
            searchHandlerWithEmptySearchList, extractHandlerWithBadMultipleFacesPolicy,
            searchHandlerWithoutSearchPriority, searchHandlerWitBadSearchPriority,
            searchHandlerWithEmptyDescriptorPolicy, searchHandlerWithoutCreatePersonPolicy,
            searchHandlerWithoutCreatePerson
        ]
        for handler in handlers:
            reply = createHandler(handler)
            self.assertEqual(reply.statusCode, 400, handler["name"])
            self.assertTrue(validate(reply.json, ERROR_SCHEMA) is None, handler["name"])

    def test_put_handler(self):
        handler = self.create_handler_to_pagination()
        reply = createHandler(handler)
        handlerId = reply.json["handler_id"]
        handler["id"] = handlerId
        handler["extract_policy"] = extractPolicyExample
        reply = putHandler(handler)
        self.assertEqual(reply.statusCode, 200, handler["name"])
        getHandlerById(handlerId)
        savingHandlerJson = getHandlerById(handlerId)
        self.assertTrue(TestHandlersAPI.compareHandlerJsons(handler, savingHandlerJson.json), handler["name"])

    def test_get_handler_not_found(self):
        reply = getHandlerById("9a89c6cf-5994-4cb5-a0d7-fbff81187319")
        self.assertEqual(reply.statusCode, 404, reply.statusCode)

    @skipWithIncrementCount("not stable")
    def test_pagination(self):
        handler = self.create_handler_to_pagination()
        handlerIds = [createHandler(handler).json["handler_id"] for i in range(12)]
        time.sleep(1)
        params = {"name": handler['name'], 'page_size': 10, 'page': 1}
        replyJson = getHandlers(params).json
        self.assertEqual(replyJson['total'], 12, 'Wrong total handlers count')
        gotHandlerIds = [handler['id'] for handler in replyJson['hits']]
        self.assertEqual(len(gotHandlerIds), 10, 'Wrong count of handlers on page')
        params['page'] = 2
        gotHandlerIds += [handler['id'] for handler in getHandlers(params).json['hits']]
        self.assertEqual(set(handlerIds), set(gotHandlerIds), 'Handler ids differ')

    def test_additional_fields(self):
        self.corrupt_test(FULL_SEARCH_HANDLER, additional_fields, createHandler)
