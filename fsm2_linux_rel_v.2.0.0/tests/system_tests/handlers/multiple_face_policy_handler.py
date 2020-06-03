from tests.system_tests.base_test_handlers_logic import BaseTestsHandlersPolicies, createTestHandler


class MultipleFacePolicyHandler(BaseTestsHandlersPolicies):

    def create_search_handler(self):
        searchHandler = {
            "name": "handlers_simple_search_handler",
            "type": "search",

            "search_policy": {
                "search_lists": [
                    {
                        "list_id": MultipleFacePolicyHandler.personsMatchingLists[0], "threshold": 0.11,
                        "list_type": "persons",
                        "limit": 1
                    }
                ],
                "search_priority": 1
            }
        }
        extractHandler = {
            "name": "test_visionlabs_handlers_multi_faces_error",
            "type": "extract",
            "multiple_faces_policy": 0
        }
        return [extractHandler, searchHandler]

    def create_multiple_face_true_handler(self):
        return {
            "name": "test_visionlabs_handlers__multi_faces_true",
            "type": "extract",
            "multiple_faces_policy": 1
        }

    def creater_multiple_faces_handler(self):
        descriptorPolicy = {
            "attach_policy": [
                {
                    "list_id": BaseTestsHandlersPolicies.descriptorsAttachLists[0],
                    "filters": {"gender": 1}
                },
                {
                    "list_id": BaseTestsHandlersPolicies.descriptorsAttachLists[1],
                    "filters": {"age_range": {"start": 10, "end": 25}}
                }
            ]
        }

        testData = {"img": "./data/girl_and_man.jpg",
                    "age_list": [BaseTestsHandlersPolicies.descriptorsAttachLists[1]],
                    "gender_list": [BaseTestsHandlersPolicies.descriptorsAttachLists[0]]}
        handler = createTestHandler("extract", name="descriptor_policy_with_one_filter",
                                    descriptorPolicy=descriptorPolicy, multipleFacesPolicy=1)

        return [testData, handler]
