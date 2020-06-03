searchPolicyExample = {
    "search_lists": [
        {"list_id": "9a89c6cf-5994-4cb5-a0d7-fbff81187319", "threshold": 0.11, "list_type": "persons", "limit": 1}],
    "search_priority": 1
}

fullFilterExample = {
    "gender": 0,
    "age_range": {"start": 1, "end": 100},
    "similarity_filter": {
        "policy": 1,
        "lists": [
            {
                "list_id": "9a89c6cf-5994-4cb5-a0d7-fbff81187319",
                "threshold": 0.9
            },
            {
                "list_id": "dc04b9e3-d7af-42a7-b4e7-475b732b325c",
                "threshold": 0.9
            }

        ]
    }
}

attachPolicyExample = [
    {
        "filters": {
            "gender": 0,
            "age_range": {"start": 1, "end": 100},
            "similarity_filter": {
                "policy": 1,
                "lists": [
                    {
                        "list_id": "9a89c6cf-5994-4cb5-a0d7-fbff81187319",
                        "threshold": 0.9
                    },
                    {
                        "list_id": "dc04b9e3-d7af-42a7-b4e7-475b732b325c",
                        "threshold": 0.9
                    }

                ]
            }
        },
        "list_id": "dc04b9e3-d7af-42a7-b4e7-475b732b325c"
    },
    {
        "filters": {
            "gender": 0,
            "age_range": {"start": 1, "end": 100},
            "similarity_filter": {
                "policy": 2,
                "lists": [
                    {
                        "list_id": "9a89c6cf-5994-4cb5-a0d7-fbff81187319",
                        "threshold": 0.9
                    },
                    {
                        "list_id": "dc04b9e3-d7af-42a7-b4e7-475b732b325c",
                        "threshold": 0.9
                    }

                ]
            }
        },
        "list_id": "dc04b9e3-d7af-42a7-b4e7-475b732b325c"
    },
    {
        "filters": {
            "gender": 1,
            "age_range": {"start": 1, "end": 100}
        },
        "list_id": "4fbc332f-25fa-402c-bd97-783c28de3aa9"

    }]

groupPolicyExample = {
    "ttl": 20,
    "grouper": 1,
    "threshold": 0.5,
    "create_person_policy": {
        "create_person": 1,
        "create_filters": fullFilterExample,
        "attach_policy": attachPolicyExample
    }
}

personPolicyExample = {
    "create_person_policy": {
        "create_person": 1,
        "create_filters": fullFilterExample,
        "attach_policy": attachPolicyExample
    }
}

extractPolicyExample = {
    "estimate_attributes": 1,
    "estimate_quality": 1,
    "score_threshold": 0.1

}

descriptorPolicyExample = {
    "attach_policy": attachPolicyExample
}

searchHandlerDescriptorPolicy = {
    "extract_policy": extractPolicyExample,
    "name": "test_visionlabs_search_descriptor_policies_handler",
    "type": "search",

    "search_policy": searchPolicyExample,
    "descriptor_policy": descriptorPolicyExample
}

searchHandlerGroupPolicy = {
    "extract_policy": extractPolicyExample,
    "name": "test_visionlabs_search_group_policies_handler",
    "type": "search",
    "search_policy": searchPolicyExample,
    "grouping_policy": groupPolicyExample

}

searchHandlerPersonPolicy = {
    "extract_policy": extractPolicyExample,
    "name": "test_visionlabs_search_person_policies_handler",
    "type": "search",
    "search_policy": searchPolicyExample,
    "person_policy": personPolicyExample
}

searchHandlerPersonDescriptorPolicy = {
    "extract_policy": extractPolicyExample,
    "name": "test_visionlabs_search_person_descriptor_policies_handler",
    "type": "search",
    "search_policy": searchPolicyExample,
    "person_policy": personPolicyExample,
    "descriptor_policy": descriptorPolicyExample
}

searchHandlerGroupDescriptorPolicy = {
    "extract_policy": extractPolicyExample,
    "name": "test_visionlabs_search_group_descriptor_policies_handler",
    "type": "search",
    "search_policy": searchPolicyExample,
    "grouping_policy": groupPolicyExample,
    "descriptor_policy": descriptorPolicyExample
}

searchHandlerIncompatibleGroupPersonPolicy = {
    "extract_policy": extractPolicyExample,
    "name": "test_visionlabs_search_incompatible_group_person_policies_handler",
    "type": "search",
    "search_policy": searchPolicyExample,
    "person_policy": personPolicyExample,
    "grouping_policy": groupPolicyExample
}

searchHandlerIncompatibleFiltersPolicy = {
    "extract_policy": {
        "estimate_attributes": 0,
        "estimate_quality": 1,
        "score_threshold": 0.1
    },
    "name": "test_visionlabs_search_incompatible_filters_policies_handler",
    "type": "search",
    "search_policy": searchPolicyExample,
    "grouping_policy": {
        "create_person_policy": {
            "create_person": 1,
            "create_filters": fullFilterExample,
            "attach_policy": attachPolicyExample
        }
    }
}

extractHandlerIncompatibleFiltersPolicy = {
    "extract_policy": {
        "estimate_attributes": 1,
        "estimate_quality": 1,
        "score_threshold": 0.1
    },
    "name": "test_visionlabs_search_incompatible_filters_policies_handler",
    "type": "extract",
    "multiple_faces_policy": 1,
    "grouping_policy": {
        "create_person_policy": {
            "create_person": 1,
            "create_filters": fullFilterExample,
            "attach_policy": attachPolicyExample
        }
    }
}

standardSearchList = {"list_id": "9a89c6cf-5994-4cb5-a0d7-fbff81187319", "threshold": 0.11, "list_type": "persons",
                      'limit': 1}

handlerWithoutType = {
    "name": "test_visionlabs_handler_without_type",
    "search_policy": {
        "search_lists": [standardSearchList],
        "search_priority": 1
    }
}

extractHandlerWithoutMultipleFacesPolicy = {
    "name": "test_visionlabs_extract_handler_without_multiple_faces_policy",
    "type": "extract"
}

extractHandlerWithBadMultipleFacesPolicy = {
    "name": "test_visionlabs_extract_handler_with_bad_multiple_faces_policy",
    "type": "extract",
    "multiple_faces_policy": 2
}

searchHandlerWithoutSearchPolicy = {
    "name": "test_visionlabs_search_handler_without_search_policy",
    "type": "search",
}

searchHandlerWithEmptySearchList = {
    "name": "test_visionlabs_search_handler_with_empty_search_lists_policy",
    "type": "search",
    "search_policy": {
        "search_lists": [],
        "search_priority": 1
    }
}

searchHandlerWithoutSearchPriority = {
    "name": "search_handler_without_search_priority",
    "type": "search",
    "search_policy": {
        "search_lists": [standardSearchList],
    }
}

searchHandlerWitBadSearchPriority = {
    "name": "search_handler_with_bad_search_priority",
    "type": "search",
    "search_policy": {
        "search_lists": [standardSearchList],
        "search_priority": 3
    }
}

searchHandlerWithEmptyDescriptorPolicy = {
    "name": "search_handler_with_empty_descriptor_policy",
    "type": "search",
    "search_policy": {
        "search_lists": [standardSearchList],
        "search_priority": 2,
    },
    "descriptor_policy": {
        "attach_policy": []
    }
}

searchHandlerWithoutCreatePersonPolicy = {
    "name": "search_handler_without_create_person_policy",
    "type": "search",
    "search_policy": {
        "search_lists": [standardSearchList],
        "search_priority": 2,
    },
    "person_policy": {}
}

searchHandlerWithoutCreatePerson = {
    "name": "search_handler_without_create__person",
    "type": "search",
    "search_policy": {
        "search_lists": [standardSearchList],
        "search_priority": 2,
    },
    "person_policy": {
        "create_person_policy": {
        }
    }
}


def searchHandlerTestEvents(name, whatToSave, inputListDescriptors, inputListPersons, outputListPersons=None,
                            outputListDescriptors=None):
    assert whatToSave in ['events', 'groups']
    cpp = {
        "create_person_policy": {
            "create_person": 1,
            "attach_policy": [{
                "list_id": outputListPersons
            }]
        }
    }
    dap = {
        "attach_policy": [
            {"list_id": outputListDescriptors}
        ]
    }
    res = {
        'name': name,
        'type': 'search',
        'extract_policy': {
            'estimate_attributes': 1
        },
        'search_policy': {
            'search_lists': [
                {
                    'list_id': inputListDescriptors,
                    'list_type': 'descriptors',
                    'threshold': 0,
                    'limit': 1
                },
                {
                    'list_id': inputListPersons,
                    'list_type': 'persons',
                    'threshold': 0,
                    'limit': 1
                }
            ],
            'search_priority': 1
        }
    }
    if outputListDescriptors is not None:
        res['descriptor_policy'] = dap
    if whatToSave == 'events':
        if outputListPersons is not None:
            res['person_policy'] = cpp
    elif whatToSave == 'groups':
        res['grouping_policy'] = {
            'ttl': 10,
            'grouper': 2,
            'threshold': 0,
        }
        if outputListPersons is not None:
            res['grouping_policy'].update(**cpp)
    return res


FULL_SEARCH_HANDLER = {
    "name": "test_visionlabs_handler_additional_fields",
    "type": "search",
    "extract_policy": {
        "estimate_quality": 0,
        "score_threshold": 0,
        "estimate_attributes": 0,
    },
    "search_policy": {
        "search_lists": [{
            "list_id": "976ebad4-8208-4cd5-a713-397b3f050ca1",
            "list_type": "descriptors",
            "threshold": 0,
            "limit": 1
        }],
        "search_priority": 1
    },
    "descriptor_policy": {
        "attach_policy": [{
            "list_id": "976ebad4-8208-4cd5-a713-397b3f050ca1",
            "filters": {
                "gender": 0,
                "age_range": {
                    "start": 0,
                    "end": 100
                },
                "similarity_filter": {
                    "policy": 1,
                    "lists": [{
                        "list_id": "976ebad4-8208-4cd5-a713-397b3f050ca1",
                        "threshold": 0
                    }]
                }
            }
        }]
    },
    "person_policy": {
        "create_person_policy": {
            "create_person": 0,
            "create_filters": {
                "gender": 0,
                "age_range": {
                    "start": 0,
                    "end": 100
                },
                "similarity_filter": {
                    "policy": 1,
                    "lists": [{
                        "list_id": "976ebad4-8208-4cd5-a713-397b3f050ca1",
                        "threshold": 0
                    }]
                }
            },
            "attach_policy": [{
                "list_id": "976ebad4-8208-4cd5-a713-397b3f050ca1",
                "filters": {
                    "gender": 0,
                    "age_range": {
                        "start": 0,
                        "end": 100
                    },
                    "similarity_filter": {
                        "policy": 1,
                        "lists": [{
                            "list_id": "976ebad4-8208-4cd5-a713-397b3f050ca1",
                            "threshold": 0
                        }]
                    }
                }
            }]
        }
    },
    "grouping_policy": {
        "ttl": 10,
        "grouper": 1,
        "age": 1,
        "gender": 1,
        "search": 1,
        "threshold": 0,
        "create_person_policy": {
            "create_person": 0,
            "create_filters": {
                "gender": 0,
                "age_range": {
                    "start": 0,
                    "end": 100
                },
                "similarity_filter": {
                    "policy": 1,
                    "lists": [{
                        "list_id": "976ebad4-8208-4cd5-a713-397b3f050ca1",
                        "threshold": 0
                    }]
                }
            },
            "attach_policy": [{
                "list_id": "976ebad4-8208-4cd5-a713-397b3f050ca1",
                "filters": {
                    "gender": 0,
                    "age_range": {
                        "start": 0,
                        "end": 100
                    },
                    "similarity_filter": {
                        "policy": 1,
                        "lists": [{
                            "list_id": "976ebad4-8208-4cd5-a713-397b3f050ca1",
                            "threshold": 0
                        }]
                    }
                }
            }]
        }
    }
}
