import uuid
from tests.system_tests.base_test_handlers_logic import BaseTestsHandlersPolicies, validate, EXTRACT_EVENT_SCHEMA


class SimplePolicyHandler(BaseTestsHandlersPolicies):

    def create_handlers_simple_handler(self, list_id=None):
        searchHandler = {
            "name": "test_visionlabs_handlers_simple_search_handler",
            "type": "search",

            "search_policy": {
                "search_lists": [
                    {
                        "list_id": list_id, "threshold": 0.11, "list_type": "persons",
                        "limit": 1
                    }
                ],
                "search_priority": 1
            }
        }
        extractHandler = {
            "name": "test_visionlabs_handlers_simple_extract_handler",
            "type": "extract",
            "multiple_faces_policy": 0
        }
        return searchHandler, extractHandler

    def create_extract_handler_non_exist_descriptor_list(self):
        return {
            "name": "test_visionlabs_handlers_simple_extract_handler",
            "type": "extract",
            "multiple_faces_policy": 0,
            "descriptor_policy":
                {"attach_policy": [
                    {"list_id": str(uuid.uuid4())}
                ]}
        }

    def create_extract_handler_non_exitst_personlist(self):
        return {
            "name": "test_visionlabs_handlers_simple_extract_handler",
            "type": "extract",
            "multiple_faces_policy": 0,
            "person_policy": {
                "create_person_policy": {
                    "create_person": 1,
                    "attach_policy": [
                        {"list_id": str(uuid.uuid4())}
                    ]
                }
            }
        }

    def create_and_get_simple_handlers(self):
        searchHandler = {
            "name": "test_visionlabs_simple_search_handler",
            "type": "search",

            "search_policy": {
                "search_lists": [
                    {"list_id": "9a89c6cf-5994-4cb5-a0d7-fbff81187319", "threshold": 0.11, "list_type": "persons",
                     "limit": 1}],
                "search_priority": 1
            }
        }
        extractHandler = {
            "name": "test_visionlabs_simple_extract_handler",
            "type": "extract",
            "multiple_faces_policy": 0
        }

        return [extractHandler, searchHandler]

    def create_handler_to_pagination(self):
        return {
            "name": "test_visionlabs_put_simple_search_handler_test_pagination",
            "type": "search",

            "search_policy": {
                "search_lists": [
                    {"list_id": "9a89c6cf-5994-4cb5-a0d7-fbff81187319", "threshold": 0.11, "list_type": "persons",
                     "limit": 1}],
                "search_priority": 1
            }
        }

    def assertErrorCode(self, reply, handler):
        self.assertEqual(reply.statusCode, 201, handler["name"])
        self.assertTrue(validate(reply.json, EXTRACT_EVENT_SCHEMA) is None, handler["name"])
        self.assertTrue(reply.json['events'][0]['error']['error_code'] == 11007, handler["name"])
