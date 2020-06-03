from tests.system_tests.base_test_handlers_logic import *


class TestDescriptorPolicy(BaseTestsHandlersPolicies):
    def test_handlers_descriptor_simple_policy(self):
        def test(testData, handlerForTest):
            eventReply = emitEvent(handlerForTest["id"], testData["img"], queryParams={"warped_image": 1})
            self.validateEvent(eventReply, handlerForTest,
                               descriptorsLists=[TestDescriptorPolicy.descriptorsAttachLists[0]])

        descriptorPolicy = {
            "attach_policy": [{"list_id": TestDescriptorPolicy.descriptorsAttachLists[0]}]
        }

        for handlerType in ["extract", "search"]:
            handler = createTestHandler(handlerType, name="simple_descriptor_policy",
                                        descriptorPolicy=descriptorPolicy)

            data = {
                "img": "./data/girl_1_0.jpg",
                "list_id": TestDescriptorPolicy.personsMatchingLists[1]
            }
            test(data, handler)

    def test_handlers_descriptor_policy_with_one_filter(self):
        def test(testData, handlerForTest):
            for imgAndList in testData:
                reply = emitEvent(handlerForTest["id"], imgAndList["img"], queryParams={"warped_image": 1})
                self.validateEvent(reply, handlerForTest,
                                   descriptorsLists=imgAndList["attaching_list"])

        for handlerType in ["extract", "search"]:
            descriptorPolicy = {
                "attach_policy": [
                    {
                        "list_id": TestDescriptorPolicy.descriptorsAttachLists[0],
                        "filters": {"gender": 1}
                    },
                    {
                        "list_id": TestDescriptorPolicy.descriptorsAttachLists[1],
                        "filters": {"age_range": {"start": 30, "end": 100}}
                    }
                ]
            }
            if handlerType == "search":
                descriptorPolicy["attach_policy"].append(
                    {
                        "list_id": TestDescriptorPolicy.descriptorsAttachLists[2],
                        "filters":
                            {
                                "similarity_filter":
                                    {
                                        "policy": 1,
                                        "lists": [
                                            {
                                                "list_id": TestDescriptorPolicy.personsMatchingLists[i],
                                                "threshold": 0.98
                                            } for i in range(3)]
                                    }
                            }
                    })

            handler = createTestHandler(handlerType, name="descriptor_policy_with_one_filter",
                                        descriptorPolicy=descriptorPolicy)

            data = [
                {
                    "img": "./data/man_young.jpg",
                    "attaching_list": [TestDescriptorPolicy.descriptorsAttachLists[0]]
                },
                {
                    "img": "./data/girl_old.jpg",
                    "attaching_list": [TestDescriptorPolicy.descriptorsAttachLists[1]]
                },

                {
                    "img": "./data/man_old.jpg",
                    "attaching_list": [TestDescriptorPolicy.descriptorsAttachLists[0],
                                       TestDescriptorPolicy.descriptorsAttachLists[1]]
                },
                {
                    "img": "./data/girl_young.jpg",
                    "attaching_list": []
                }
            ]
            if handlerType == "search":
                data.append({
                    "img": "./data/girl_1_2.jpg",
                    "attaching_list": [TestDescriptorPolicy.descriptorsAttachLists[2]]
                })

            test(data, handler)

    def test_handlers_descriptor_policy_with_similarity_filter_2(self):
        def test(testData, handlerForTest):
            for imgAndList in testData:
                reply = emitEvent(handlerForTest["id"], imgAndList["img"], queryParams={"warped_image": 1})
                self.validateEvent(reply, handlerForTest,
                                   descriptorsLists=imgAndList["attaching_list"])

        descriptorPolicy = {
            "attach_policy": [
                {
                    "list_id": TestDescriptorPolicy.descriptorsAttachLists[2],
                    "filters":
                        {
                            "similarity_filter":
                                {
                                    "policy": 2,
                                    "lists": [{
                                        "list_id": TestDescriptorPolicy.personsMatchingLists[i],
                                        "threshold": 0.8
                                    } for i in range(3)]
                                }
                        }
                }
            ]
        }

        for handlerType in ["search"]:
            handler = createTestHandler(handlerType, name="descriptor_policy_with_similarity_filter_2",
                                        descriptorPolicy=descriptorPolicy)

            data = [
                {
                    "img": "./data/girl_1_2.jpg",
                    "attaching_list": []
                },
                {
                    "img": "./data/girl_young.jpg",
                    "attaching_list": [TestDescriptorPolicy.descriptorsAttachLists[2]]
                }
            ]
            test(data, handler)

    def test_handlers_descriptor_policy_with_several_filters(self):
        def test(testData, handlerForTest):
            for imgAndList in testData:
                reply = emitEvent(handlerForTest["id"], imgAndList["img"], queryParams={"warped_image": 1})
                self.validateEvent(reply, handlerForTest,
                                   descriptorsLists=imgAndList["attaching_list"])

        for handlerType in ["extract", "search"]:

            descriptorPolicy = {
                "attach_policy": [
                    {
                        "list_id": TestDescriptorPolicy.descriptorsAttachLists[0],
                        "filters": {"gender": 0}
                    },
                    {
                        "list_id": TestDescriptorPolicy.descriptorsAttachLists[1],
                        "filters": {"age_range": {"start": 30, "end": 100},
                                    "gender": 0}
                    }

                ]
            }
            data = [
                {
                    "img": "./data/girl_young.jpg",
                    "attaching_list": [TestDescriptorPolicy.descriptorsAttachLists[0]]
                },
                {
                    "img": "./data/girl_old.jpg",
                    "attaching_list": [TestDescriptorPolicy.descriptorsAttachLists[1],
                                       TestDescriptorPolicy.descriptorsAttachLists[0]]
                },

                {
                    "img": "./data/man_old.jpg",
                    "attaching_list": []
                },
            ]

            if handlerType == "search":
                descriptorPolicy["attach_policy"].append({
                    "list_id": TestDescriptorPolicy.descriptorsAttachLists[2],
                    "filters":
                        {
                            "gender": 0,
                            "age_range": {"start": 16, "end": 100},
                            "similarity_filter":
                                {
                                    "policy": 1,
                                    "lists": [{
                                        "list_id": matchingList,
                                        "threshold": 0.99
                                    } for matchingList in TestDescriptorPolicy.personsMatchingLists]
                                }
                        }
                })
                data.append({
                    "img": "./data/girl_1_0.jpg",
                    "attaching_list": [TestDescriptorPolicy.descriptorsAttachLists[2],
                                       TestDescriptorPolicy.descriptorsAttachLists[0]]
                })
            handler = createTestHandler(handlerType, name="descriptor_policy_with_similarity_filter_2",
                                        descriptorPolicy=descriptorPolicy)

            test(data, handler)
