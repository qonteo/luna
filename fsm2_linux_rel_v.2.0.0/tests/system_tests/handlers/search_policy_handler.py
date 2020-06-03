from tests.system_tests.base_test_handlers_logic import BaseTestsHandlersPolicies, createTestSearchHandler, \
    createHandler, emitEvent


class SearchPolicyHandler(BaseTestsHandlersPolicies):

    def create_handler_search_by_3_list(self):
        searchHandlerPersonsLists = createTestSearchHandler(
            "search_by_3_list_persons",
            [
                {
                    "list_id": SearchPolicyHandler.personsMatchingLists[i],
                    "threshold": 0.11,
                    "list_type": "persons",
                    "limit": 1
                } for i in range(3)])
        searchHandlerDescriptorsLists = createTestSearchHandler(
            "search_by_3_list_descriptors",
            [
                {
                    "list_id": SearchPolicyHandler.descriptorsMatchingLists[i],
                    "threshold": 0.11,
                    "list_type": "descriptors",
                    "limit": 1
                } for i in range(3)])

        return [
            {
                "handler": searchHandlerPersonsLists,
                "data": [{
                    "img": "./data/girl_1_{}.jpg".format(i),
                    "list_id": SearchPolicyHandler.personsMatchingLists[i]
                } for i in range(3)]
            },
            {
                "handler": searchHandlerDescriptorsLists,
                "data": [{
                    "img": "./data/girl_2_{}.jpg".format(i),
                    "list_id": SearchPolicyHandler.descriptorsMatchingLists[i]
                } for i in range(3)]
            }
        ]

    def create_handlers_search_priority_2(self):
        searchHandlerPersonsListsPriority2 = createTestSearchHandler(
            "search_by_3_list_persons_with_priority_2",
            [
                {
                    "list_id": SearchPolicyHandler.personsMatchingLists[i],
                    "threshold": 1,
                    "list_type":
                        "persons",
                    "limit": 1
                } for i in range(3)],
            2
        )
        searchHandlerDescriptorsListsPriority2 = createTestSearchHandler(
            "search_by_3_list_descriptors_with_priority_2",
            [{
                "list_id":
                    SearchPolicyHandler.descriptorsMatchingLists[i],
                "threshold": 1,
                "list_type": "descriptors",
                "limit": 1
            } for i in range(3)],
            2
        )

        return [
            {
                "handler": searchHandlerPersonsListsPriority2,
                "data": [{
                    "img": "./data/girl_1_{}.jpg".format(i),
                    "list_id": SearchPolicyHandler.personsMatchingLists[i]
                } for i in range(3)]
            },
            {
                "handler": searchHandlerDescriptorsListsPriority2,
                "data": [{
                    "img": "./data/girl_2_{}.jpg".format(i),
                    "list_id": SearchPolicyHandler.descriptorsMatchingLists[i]
                } for i in range(3)]
            }
        ]

    def create_handlers_search_persons(self):
        searchHandlerPersonsAndDescriptorsLists = createTestSearchHandler(
            "search_by_persons_and_descriptors_lists",
            [
                {
                    "list_id": SearchPolicyHandler.personsMatchingLists[i] if i % 2 == 0 else
                    SearchPolicyHandler.descriptorsMatchingLists[i],
                    "threshold": 0.11,
                    "list_type": "persons" if i % 2 == 0 else "descriptors",
                    "limit": 1
                }
                for i in range(3)]
        )

        return [
            {
                "handler": searchHandlerPersonsAndDescriptorsLists,
                "data": [{
                    "img": "./data/girl_{}_{}.jpg".format(1 if i % 2 == 0 else 2, i),
                    "list_id": SearchPolicyHandler.personsMatchingLists[i] if i % 2 == 0 else
                    SearchPolicyHandler.descriptorsMatchingLists[i]
                } for i in range(3)]
            }
        ]

    def create_event(self, warped_flag, handlersAndData):
        handlers = []
        for handlerAndData in handlersAndData:
            handler = handlerAndData["handler"]
            reply = createHandler(handler)
            handlerId = reply.json["handler_id"]
            for count, data in enumerate(handlerAndData["data"]):
                reply = emitEvent(
                    handlerId, data["img"],
                    queryParams={"warped_image": warped_flag},
                    # //todo requests_method=RequestMethod.POST
                )
                if warped_flag == 0:
                    self.assertEqual(len(reply.json["events"][0]["search"]), 3, handler["name"])

                handlers.append([reply, handler, data])
        return handlers
