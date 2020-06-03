from tests.system_tests.base_test_handlers_logic import BaseTestsHandlersPolicies, createTestHandler


class PersonPolicyHandler(BaseTestsHandlersPolicies):

    def create_handlers_person_policy_or_person_policy_user_data(self, policyname):
        handlers = []
        personPolicy = {
            "create_person_policy": {"create_person": 1}
        }
        for handlerType in ["extract", "search"]:
            handler = createTestHandler(handlerType, name=policyname,
                                        personPolicy=personPolicy)

            data = [{
                "img": "./data/girl_1_0.jpg",
                "list_id": PersonPolicyHandler.personsMatchingLists[0]
            }]
            handlers.append([data, handler])
        return handlers

    def create_handlers_person_with_filters(self):
        handlers = []
        for handlerType in ["extract", "search"]:
            personPolicies = [
                {
                    "create_person_policy":
                        {
                            "create_person": 1,
                            "create_filters":
                                {
                                    "gender": 1
                                }
                        }
                },
                {
                    "create_person_policy":
                        {
                            "create_person": 1,
                            "create_filters":
                                {
                                    "age_range": {"start": 30, "end": 60}
                                }
                        }
                },
            ]
            if handlerType == "search":
                personPolicies.append({
                    "create_person_policy":
                        {
                            "create_person": 1,
                            "create_filters":
                                {
                                    "similarity_filter":
                                        {
                                            "policy": 1,
                                            "lists": [{
                                                "list_id": matchingList,
                                                "threshold": 0.99
                                            } for matchingList in PersonPolicyHandler.personsMatchingLists]
                                        }
                                }
                        }
                })
            created_handlers = []
            for count, personPolicy in enumerate(personPolicies):
                handler = createTestHandler(handlerType, name="create_person_with_filter_{}".format(count),
                                            personPolicy=personPolicy)

                created_handlers.append(handler)

            data = [
                "./data/man_young.jpg",
                "./data/girl_old.jpg"
            ]
            if handlerType == "search":
                data.append("./data/girl_1_0.jpg")

            handlers.append([data, created_handlers])
        return handlers

    def create_handlers_person_create_with_several_filters(self):
        handlers = []
        for handlerType in ["extract", "search"]:
            personPolicy = {
                "create_person_policy":
                    {
                        "create_person": 1,
                        "create_filters":
                            {
                                "gender": 0,
                                "age_range": {"start": 21, "end": 22},
                            }
                    }
            }
            if handlerType == "search":
                personPolicy["create_person_policy"]["create_filters"]["similarity_filter"] = {
                    "policy": 1,
                    "lists": [{
                        "list_id": matchingList,
                        "threshold": 0.99
                    } for matchingList in PersonPolicyHandler.personsMatchingLists]
                }

            handler = createTestHandler(handlerType,
                                        name="test_visionlabs_extract_handler_create_person_with_several_filters",
                                        personPolicy=personPolicy)

            data = [
                "./data/girl_1_1.jpg",
                "./data/girl_1_0.jpg",
            ]
            handlers.append([data, handler])
        return handlers

    def create_handlers_person_with_similarity_policy_2(self):
        handlers = []
        personPolicy = {
            "create_person_policy":
                {
                    "create_person": 1,
                    "create_filters":
                        {
                            "gender": 0,
                            "age_range": {"start": 1, "end": 30},
                            "similarity_filter":
                                {
                                    "policy": 2,
                                    "lists": [{
                                        "list_id": matchingList,
                                        "threshold": 0.8
                                    } for matchingList in PersonPolicyHandler.personsMatchingLists]

                                }
                        }
                }
        }

        for handlerType in ["search"]:
            handler = createTestHandler(handlerType,
                                        name="create_person_with_similarity_policy_2",
                                        personPolicy=personPolicy
                                        )

            data = [
                "./data/girl_1_1.jpg",
                "./data/girl_young.jpg",
            ]
            handlers.append([data, handler])
        return handlers

    def create_handlers_person_attach_simple(self):
        created_handlers = []

        personPolicy = {
            "create_person_policy": {"create_person": 1,
                                     "attach_policy": [{"list_id": PersonPolicyHandler.personsAttachLists[0]}]}
        }

        handlers = []
        for handlerType in ["extract", "search"]:
            handler = createTestHandler(handlerType, name="simple_person_attach_policy",
                                        personPolicy=personPolicy)

            data = {
                "img": "./data/girl_1_1.jpg"
            }
            handlers.append([data, handler])
        created_handlers.append(handlers)

        return created_handlers

    def create_handlers_person_attach_policy_with_one_filter(self):
        handlers = []
        for handlerType in ["extract", "search"]:
            personPolicy = {
                "create_person_policy": {
                    "create_person": 1,
                    "attach_policy": [
                        {
                            "list_id": PersonPolicyHandler.personsAttachLists[0],
                            "filters": {"gender": 1}
                        },
                        {
                            "list_id": PersonPolicyHandler.personsAttachLists[1],
                            "filters": {"age_range": {"start": 30, "end": 100}}
                        }
                    ]
                }
            }
            data = [
                {
                    "img": "./data/man_young.jpg",
                    "attaching_list": [PersonPolicyHandler.personsAttachLists[0]]
                },
                {
                    "img": "./data/girl_old.jpg",
                    "attaching_list": [PersonPolicyHandler.personsAttachLists[1]]
                },
                {
                    "img": "./data/girl_young.jpg",
                    "attaching_list": []
                }
            ]

            simFilter = {
                "list_id": PersonPolicyHandler.personsAttachLists[2],
                "filters":
                    {
                        "similarity_filter":
                            {
                                "policy": 1,
                                "lists": [{
                                    "list_id": matchingList,
                                    "threshold": 0.8
                                } for matchingList in PersonPolicyHandler.personsMatchingLists]
                            }
                    }
            }
            if handlerType == "search":
                personPolicy["create_person_policy"]["attach_policy"].append(simFilter)
                data.append({
                    "img": "./data/girl_1_2.jpg",
                    "attaching_list": [PersonPolicyHandler.personsAttachLists[2]]
                })
                data.append({
                    "img": "./data/man_old.jpg",
                    "attaching_list": [PersonPolicyHandler.personsAttachLists[0],
                                       PersonPolicyHandler.personsAttachLists[1]]
                })

            handler = createTestHandler(handlerType, name="person_attach_with_one_filter",
                                        personPolicy=personPolicy)
            handlers.append([data, handler])
        return handlers

    def create_handlers_person_attach_policy_with_several_filters(self):
        handlers = []
        for handlerType in ["extract", "search"]:
            personPolicy = {
                "create_person_policy": {
                    "create_person": 1,
                    "attach_policy": [
                        {
                            "list_id": PersonPolicyHandler.personsAttachLists[0],
                            "filters": {"gender": 0}
                        },
                        {
                            "list_id": PersonPolicyHandler.personsAttachLists[1],
                            "filters": {"age_range": {"start": 30, "end": 100},
                                        "gender": 0}
                        }
                    ]
                }
            }
            simFilter = {
                "list_id": PersonPolicyHandler.personsAttachLists[2],
                "filters":
                    {
                        "gender": 0,
                        "age_range": {"start": 16, "end": 100},
                        "similarity_filter":
                            {
                                "policy": 1,
                                "lists": [{
                                    "list_id": matchingList,
                                    "threshold": 0.98
                                } for matchingList in PersonPolicyHandler.personsMatchingLists]
                            }
                    }
            }
            data = [
                {
                    "img": "./data/girl_young.jpg",
                    "attaching_list": [PersonPolicyHandler.personsAttachLists[0]]
                },
                {
                    "img": "./data/man_old.jpg",
                    "attaching_list": []
                },
            ]
            if handlerType == "search":
                personPolicy["create_person_policy"]["attach_policy"].append(simFilter)
                data.append({
                    "img": "./data/girl_old.jpg",
                    "attaching_list": [PersonPolicyHandler.personsAttachLists[1],
                                       PersonPolicyHandler.personsAttachLists[0]]
                })
                data.append({
                    "img": "./data/girl_1_0.jpg",
                    "attaching_list": [PersonPolicyHandler.personsAttachLists[2],
                                       PersonPolicyHandler.personsAttachLists[0]]
                })

            handler = createTestHandler(handlerType, name="person_attach_with_several_filters",
                                        personPolicy=personPolicy)

            handlers.append([data, handler])
        return handlers

    def create_handlers_person_attach_policy_with_one_filter2(self):
        handlers = []
        for handlerType in ["extract", "search"]:
            personPolicy = {
                "create_person_policy": {
                    "create_person": 1,
                    "attach_policy": [
                        {
                            "list_id": PersonPolicyHandler.personsAttachLists[0],
                            "filters": {"gender": 1}
                        },
                        {
                            "list_id": PersonPolicyHandler.personsAttachLists[1],
                            "filters": {"age_range": {"start": 30, "end": 100}}
                        }
                    ]
                }
            }
            data = [
                {
                    "img": "./data/man_young.jpg",
                    "attaching_list": [PersonPolicyHandler.personsAttachLists[0]]
                },
                {
                    "img": "./data/girl_old.jpg",
                    "attaching_list": [PersonPolicyHandler.personsAttachLists[1]]
                },
                {
                    "img": "./data/girl_young.jpg",
                    "attaching_list": []
                }
            ]

            simFilter = {
                "list_id": PersonPolicyHandler.personsAttachLists[2],
                "filters":
                    {
                        "similarity_filter":
                            {
                                "policy": 1,
                                "lists": [{
                                    "list_id": matchingList,
                                    "threshold": 0.8
                                } for matchingList in PersonPolicyHandler.personsMatchingLists]
                            }
                    }
            }
            if handlerType == "search":
                personPolicy["create_person_policy"]["attach_policy"].append(simFilter)
                data.append({
                    "img": "./data/girl_1_2.jpg",
                    "attaching_list": [PersonPolicyHandler.personsAttachLists[2]]
                })
                data.append({
                    "img": "./data/man_old.jpg",
                    "attaching_list": [PersonPolicyHandler.personsAttachLists[0],
                                       PersonPolicyHandler.personsAttachLists[1]]
                })

            handler = createTestHandler(handlerType, name="person_attach_with_one_filter",
                                        personPolicy=personPolicy)

            handlers.append([data, handler])
        return handlers
