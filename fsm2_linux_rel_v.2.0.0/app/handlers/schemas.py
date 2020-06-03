import copy

uuid_pattern = "^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$"

UUID_TYPE = {"type": "string", "pattern": uuid_pattern}

BASE_FILTERS = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "gender":
            {
                "type": "integer",
                "enum": [0, 1]
            },
        "age_range": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "start": {"type": "integer",
                          "minimum": 0,
                          "maximum": 100},
                "end": {"type": "integer",
                        "minimum": 0,
                        "maximum": 100}
            }
        },

        "similarity_filter": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "policy": {
                    "type": "integer",
                    "enum": [1, 2]
                },
                "lists": {
                    "type": "array",
                    "items": {
                        "additionalProperties": False,
                        "type": "object",
                        "properties": {
                            "list_id": {"type": "string", "pattern": uuid_pattern},
                            "threshold": {"type": "number",
                                          "minimum": 0,
                                          "maximum": 1}
                        },
                        "required": ["list_id", "threshold"]
                    },
                    "minItems": 1

                }
            },
            "required": ["policy", "lists"]
        }
    },
    "minProperties": 1
}

ATTACH_LIST_RULES = {
    "type": "object",
    "properties": {
        "list_id": {"type": "string", "pattern": uuid_pattern},
        "filters": BASE_FILTERS
    },
    "required": ["list_id"],
    "additionalProperties": False,
}

CREATE_PERSON_POLICY = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "create_person": {"type": "integer",
                          "enum": [0, 1]},
        "create_filters": BASE_FILTERS,
        "attach_policy": {
            "type": "array",
            "items": ATTACH_LIST_RULES,
            "minItems": 1
        }
    }, "required": ["create_person"]

}
BASE_HANDLER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},

        "extract_policy": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "estimate_quality": {"type": "integer",
                                     "enum": [0, 1]},
                "estimate_attributes": {"type": "integer",
                                        "enum": [0, 1]},
                "score_threshold": {"type": "number",
                                    "minimum": 0,
                                    "maximum": 1},

            },
            "minProperties": 1
        },
        "grouping_policy": {
            "type": "object",
            "additionalProperties": False,
            "properties":
                {
                    "age": {
                        "type": "integer",
                        "enum": [1]
                    },
                    "gender": {
                        "type": "integer",
                        "enum": [1, 2]
                    },
                    "search": {
                        "type": "integer",
                        "enum": [1, 2, 3]
                    },
                    "grouper": {
                        "type": "integer",
                        "enum": [1, 2, 3]
                    },
                    "ttl": {
                        "type": "integer",
                        "minimum": 3,
                        "maximum": 3600
                    },
                    "threshold": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "create_person_policy": CREATE_PERSON_POLICY
                }, "required": ["grouper", "ttl", "threshold"]
        },
        "person_policy": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "create_person_policy": CREATE_PERSON_POLICY
            }, "required": ["create_person_policy"]

        },
        "descriptor_policy": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "attach_policy": {
                    "type": "array",
                    "minItems": 1,
                    "items": ATTACH_LIST_RULES,

                }
            }, "required": ["attach_policy"]
        },
    }
}

CREATE_SEARCH_SCHEMA = copy.deepcopy(BASE_HANDLER_SCHEMA)
CREATE_SEARCH_SCHEMA["required"] = ["search_policy", "type"]
CREATE_SEARCH_SCHEMA["properties"]["type"] = {
    "type": "string",
    "enum": ["search"]}
CREATE_SEARCH_SCHEMA["properties"]["search_policy"] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "search_lists": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "list_id": {"type": "string", "pattern": uuid_pattern},
                    "threshold": {"type": "number",
                                  "minimum": 0,
                                  "maximum": 1},
                    "list_type": {"type": "string",
                                  "enum": ["descriptors", "persons"]},
                    "limit": {"type": "integer",
                              "minimum": 1,
                              "maximum": 5
                              }
                },
                "required": ["list_id", "threshold", "list_type", "limit"]
            }
        },
        "search_priority": {
            "type": "integer",
            "enum": [1, 2]
        }
    },
    "required": ["search_lists", "search_priority"]
}

UPDATE_SEARCH_SCHEMA = copy.deepcopy(CREATE_SEARCH_SCHEMA)
UPDATE_SEARCH_SCHEMA["properties"]["id"] = {"type": "string", "pattern": uuid_pattern}
UPDATE_SEARCH_SCHEMA["required"].append("id")

CREATE_EXTRACT_SCHEMA = copy.deepcopy(BASE_HANDLER_SCHEMA)
CREATE_EXTRACT_SCHEMA["required"] = ["multiple_faces_policy", "type"]
CREATE_EXTRACT_SCHEMA["properties"]["type"] = {
    "type": "string",
    "enum": ["extract"]
}

CREATE_EXTRACT_SCHEMA["properties"]["multiple_faces_policy"] = {"type": "integer",
                                                                "enum": [0, 1]}

UPDATE_EXTRACT_SCHEMA = copy.deepcopy(CREATE_EXTRACT_SCHEMA)
UPDATE_EXTRACT_SCHEMA["properties"]["id"] = {"type": "string", "pattern": uuid_pattern}
UPDATE_EXTRACT_SCHEMA["required"].append("id")

TOP_N_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "top_n": {
            "type": "integer",
            "minimum": 1,
        },
        "list_id": UUID_TYPE,
        "description":
            {"type": "string"}
    },
    "required": ["list_id", "top_n"]
}

_LINKER_LIST_TO_LIST = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "description": {"type": "string"},
        "object": {"type": "string", "enum": ["luna_list"]},
        "list_type": {"type": "string", "enum": ["descriptors", "persons"]},
        "list_id": UUID_TYPE,
        "list_data": {"type": "string"},
        "filters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "list_id": UUID_TYPE
            },
            "required": ['list_id'],
        }
    },
    "oneOf": [
        {"required": ['object', 'list_type', 'list_id', 'filters']},
        {"required": ['object', 'list_type', 'list_data', 'filters']},
    ]
}

date_time_pattern = "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
DATE_TIME_TYPE = {'type': "string", "pattern": date_time_pattern}

_OBJECTS_FILTERS = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string"},
        },
        "age__lt": {
            "type": "number",
            "minimum": 0,
        },
        "age__gt": {
            "type": "number",
            "minimum": 0,
        },
        "create_time__gt": DATE_TIME_TYPE,
        "create_time__lt": DATE_TIME_TYPE,
        "sources": {
            "type": "array",
            "items": {"type": "string"}
        },
        "similarity__gt": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        },
        "similarity__lt": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        },
        "handler_ids": {
            "type": "array",
            "items": UUID_TYPE,
        },
        "gender": {
            "enum": [1, 0],
        },
    },
}

_LINKER_GROUPS_TO_LIST = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "object": {"type": "string", "enum": ["groups"]},
        "list_type": {"type": "string", "enum": ["persons"]},
        "list_id": UUID_TYPE,
        "list_data": {"type": "string"},
        "filters": _OBJECTS_FILTERS,
        "description": {"type": "string"}
    },
    "oneOf": [
        {"required": ['object', 'list_type', 'list_id', 'filters']},
        {"required": ['object', 'list_type', 'list_data', 'filters']},
    ]
}

_LINKER_EVENTS_TO_LIST = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "object": {"type": "string", "enum": ["events"]},
        "list_type": {"type": "string", "enum": ["descriptors", "persons"]},
        "list_id": UUID_TYPE,
        "list_data": {"type": "string"},
        "filters": _OBJECTS_FILTERS,
        "description": {"type": "string"}
    },
    "oneOf": [
        {"required": ['object', 'list_type', 'list_id', 'filters']},
        {"required": ['object', 'list_type', 'list_data', 'filters']},
    ],
}


LINKER_SCHEMA = {
    "oneOf": [
        _LINKER_LIST_TO_LIST,
        _LINKER_GROUPS_TO_LIST,
        _LINKER_EVENTS_TO_LIST
    ]
}

_CROSS_MATCHER_REFERENCES_LIST = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "objects": {
            "type": "string",
            "enum": ["luna_list", "events", "groups"]
        },
        "filters": _OBJECTS_FILTERS
    },
    "required": ["objects", "filters"],
}
_CROSS_MATCHER_LUNA_LIST = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "objects": {
            "type": "string",
            "enum": ["luna_list"]
        },
        "filters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "list_id": UUID_TYPE
            },
            "required": ["list_id"],
        }
    },
    "required": ["objects", "filters"],
}

CROSS_MATCHER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "description": {"type": "string"},
        "threshold": {"type": "number"},
        "limit": {"type": "integer"},
        "references": {
            "oneOf": [
                _CROSS_MATCHER_REFERENCES_LIST,
                _CROSS_MATCHER_LUNA_LIST
            ]
        },
        "candidates": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "list_id": UUID_TYPE
            },
            "required": ['list_id']
        }
    },
    "required": ["references", "candidates"],
}

CLUSTERIZATION_SCHEMA_LIST = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "description": {"type": "string"},
        "objects": {
            "type": "string",
            "enum": ["luna_list"]
        },
        "filters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "list_id": UUID_TYPE
            },
            "required": ["list_id"],
        }
    },
    "required": ["filters", "objects"],
}

CLUSTERIZATION_SCHEMA_OBJECT = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "description": {"type": "string"},
        "objects": {
            "type": "string",
            "enum": ["events", "groups"]
        },
        "filters": _OBJECTS_FILTERS,
        "threshold": {'type': "number", "minimum": 0, "maximum": 1}
    },
    "required": ["filters", "objects"],
}

REPORTER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "description": {"type": "string"},
        'task_id': {"type": "integer"},
        'format': {
            "type": "string",
            "enum": ['pdf', 'csv']
        },
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                'save_portraits': {"type": "integer", "enum": [1, 0]},
                'colors_bounds': {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "green": {"type": "number"},
                        "orange": {"type": "number"},
                        "red": {"type": "number"},
                    },
                },
            },
        },
    },
    "required": ["task_id", "format"],
}
