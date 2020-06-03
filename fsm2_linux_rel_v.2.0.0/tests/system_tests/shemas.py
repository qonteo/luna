import copy

uuid_pattern = "^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$"

TYPE_UUID4 = {"type": "string", "pattern": uuid_pattern}
TYPE_NULL = {"type": "null"}

CREATE_HANDLER_SCHEMAS = {
    "type": "object",
    "properties":
        {
            "handler_id": TYPE_UUID4
        },
    "required": ["handler_id"]
}

ERROR_SCHEMA = {
    "type": "object",
    "properties":
        {
            "error_code": {"type": "integer"},
            "detail": {"type": "string"},
        },
    "required": ["error_code", "detail"]
}

RECT_SCHEMA = {
    "type": "object",
    "properties": {
        "height": {"type": "integer"},
        "width": {"type": "integer"},
        "x": {"type": "integer"},
        "y": {"type": "integer"}
    }, "required": ["height", "width", "x", "y"]
}
ATTRIBUTES_SCHEMA = {
    "type": "object",
    "properties":
        {
            "age": {
                "type": "number",
                "minimum": 0,
                "maximum": 100
            },
            "gender": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            },
            "eyeGlasses": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            }
        }
}

FACE_SCHEMA = \
    {
        "type": "object",
        "properties":
            {
                "id": TYPE_UUID4,
                "rect": RECT_SCHEMA,
                "rectISO": RECT_SCHEMA,
                "score":
                    {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                "quality":
                    {
                        "type": "object",
                        "properties":
                            {
                                "blurriness": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1
                                },
                                "dark": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1
                                },
                                "light": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1
                                },
                                "saturation": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1
                                }
                            },
                        "required": ["blurriness", "dark", "light", "saturation"]

                    },
                "attributes": ATTRIBUTES_SCHEMA
            },
        "required": ["id"]
    }

SEARCH_RESULT_PERSON = {
    "type": "object",
    "properties": {
        "person_id": TYPE_UUID4,
        "descriptor_id": TYPE_UUID4,
        "user_data": {"type": "string"},
        "similarity": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        }
    }, "required": ["person_id", "descriptor_id", "user_data", "similarity"]
}

SEARCH_RESULT_DESCRIPTOR = {
    "type": "object",
    "properties": {
        "id": TYPE_UUID4,
        "similarity": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        }
    }, "required": ["id", "similarity"]
}

SEARCH_BY_GROUP = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": SEARCH_RESULT_DESCRIPTOR

        }
    }, "required": ["candidates"]
}

EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties":
                    {
                        "id": TYPE_UUID4,
                        "descriptor_id": TYPE_UUID4,
                        "person_id":
                            {
                                "anyOf": [
                                    TYPE_UUID4,
                                    TYPE_NULL
                                ]
                            },
                        "user_data":
                            {
                                "anyOf": [
                                    {"type": "string"},
                                    TYPE_NULL
                                ]
                            },
                        "source":
                            {
                                "anyOf": [
                                    {"type": "string"},
                                    TYPE_NULL
                                ]
                            },
                        "group_id":
                            {
                                "anyOf": [
                                    TYPE_UUID4,
                                    TYPE_NULL
                                ]
                            },
                        "external_id":
                            {
                                "anyOf": [
                                    {
                                        "type": "string"
                                    }
                                    ,
                                    TYPE_NULL
                                ]
                            },
                        "tags":
                            {
                                "anyOf": [
                                    {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    TYPE_NULL
                                ]
                            },
                        "create_time": {"type": "string", "format": "date-time"},
                        "handler_id": TYPE_UUID4,
                        "persons_lists":
                            {
                                "type": "array",
                                "items": TYPE_UUID4
                            },
                        "descriptors_lists":
                            {
                                "type": "array",
                                "items": TYPE_UUID4
                            },
                        "extract": FACE_SCHEMA,
                        "search_by_group":
                            {
                                "anyOf": [
                                    SEARCH_BY_GROUP,
                                    TYPE_NULL
                                ]
                            }

                    },
                "required": ["id", "descriptor_id", "person_id", "handler_id", "create_time", "tags", "persons_lists",
                             "descriptors_lists", "external_id", "group_id", "user_data", "extract", "source"
                             ]
            }
        }
    }, "required": ["events"]
}

SEARCH_EVENT_SCHEMA = copy.deepcopy(EVENT_SCHEMA)
SEARCH_EVENT_SCHEMA["properties"]["events"]["items"]["properties"]["search"] = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "list_id": TYPE_UUID4,
            "candidates": {
                "anyOf": [
                    {
                        "type": "array",
                        "items": SEARCH_RESULT_PERSON
                    },
                    {
                        "type": "array",
                        "items": SEARCH_RESULT_DESCRIPTOR
                    }
                ]

            }
        }
    }
}
SEARCH_EVENT_SCHEMA["properties"]["events"]["items"]["required"].append("search")

EXTRACT_EVENT_SCHEMA = copy.deepcopy(EVENT_SCHEMA)
EXTRACT_EVENT_SCHEMA["properties"]["events"]["items"]["properties"]["search"] = {"type": "null"}
EXTRACT_EVENT_SCHEMA["properties"]["events"]["items"]["required"].append("search")

GROUP_SCHEMA = {
    "type": "object",
    "properties": {
        "id": TYPE_UUID4,
        "descriptor_id": TYPE_UUID4,
        "person_id":
            {
                "anyOf": [
                    TYPE_UUID4,
                    TYPE_NULL
                ]
            },
        "create_time": {"type": "string", "format": "date-time"},
        "last_update": {"type": "string", "format": "date-time"},
        "handler_id": TYPE_UUID4,
        "persons_lists":
            {
                "type": "array",
                "items": TYPE_UUID4
            },
        "descriptors": {
            "type": "array",
            "items": TYPE_UUID4,
            "minItems": 1
        },
        "source": {
            "anyOf": [
                {
                    "type": "string"
                },
                TYPE_NULL
            ]},
        "ttl": {"type": "integer"},
        "external_tracks_id": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "attributes": {
            "type": "object",
            "properties": {

                "age": {"anyOf": [
                    {"type": "number",
                     "minimum": 0,
                     "maximum": 100
                     }, TYPE_NULL]},
                "gender": {
                    "anyOf": [{
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1},
                        TYPE_NULL]
                }
            }, "required": ["age", "gender"]
        }
    },
    "required": ["id", "person_id", "handler_id", "attributes", "ttl", "external_tracks_id",
                 "source", "descriptors", "last_update", "create_time", "persons_lists"
                 ]
}

MULTI_FACE_ERROR = {
    "type": "object",
    "properties": {
        "description": {
            "type": "string"
        },
        "event_id": TYPE_UUID4,
        "faces": {
            "type": "array",
            "items": FACE_SCHEMA,
            "minItems": 2
        }
    },
    "required": ["description", "event_id", "faces"]
}

MULTI_FACE_FSM_ERROR = {
    "type": "object",
    "properties": {
        "error_code": {"type": "integer"},
        "detail": MULTI_FACE_ERROR
    },
    "required": ["error_code", "detail"]
}

TASK_SCHEMA = {
    "type": "object",
    "properties":
        {
            "id":
                {
                    "type": "integer",
                    "minimum": 0

                },
            "progress":
                {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                },
            "status":
                {
                    "type": "string",
                    "enum": ["started", "in progress", "failed", "done", "cancelled"]
                },
            "type":
                {
                    "type": "string",
                    "enum": ["hit_top_n", "clusterization", "linking"]
                },
            "create_time": {"type": "string", "format": "date-time"},
            "last_update": {"type": "string", "format": "date-time"},
            "result": {
                "type": "object",
                "properties": {
                    "errors": {
                        "type": "object",
                        "properties": {
                            "total": {
                                "type": "integer",
                                "minimum": 0

                            },
                            "errors": {
                                "type": "array",
                                "items": ERROR_SCHEMA,
                            }
                        }

                    }
                }

            }
        },
    "required": ["id", "progress", "status", "type", "create_time", "last_update"]
}

TASK_HIT_TOP_N_SCHEMA = copy.deepcopy(TASK_SCHEMA)
TASK_HIT_TOP_N_SCHEMA["properties"]["result"]["properties"]["success"] = {
    "type": "object",
    "properties": {
        "tops": {
            "type": "array",
            "items": {
                "type": "number",
                "minimum": 0,
                "maximum": 1
            },
            "minItems": 1
        },
        "total": {
            "type": "number",
            "minimum": 1
        }
    },
    "required": ["tops", "total"]
}
TASK_HIT_TOP_N_SCHEMA["properties"]["type"]["enum"] = ["hit_top_n"]
TASK_HIT_TOP_N_SCHEMA["properties"]["status"]["enum"] = ["done"]
TASK_HIT_TOP_N_SCHEMA["properties"]["progress"]["minimum"] = 1
TASK_HIT_TOP_N_SCHEMA["required"].append("result")
TASK_HIT_TOP_N_SCHEMA["properties"]["result"]["required"] = ["success"]

VERSIONSCHEMA = {
    "type": "object",
    "properties": {
        "facestreammanager2": {
            "type": "object",
            "properties": {
                "minor": {
                    "type": "number",
                    "minimum": 0
                },
                "major": {
                    "type": "number",
                    "minimum": 0
                },
                "patch": {
                    "type": "number",
                    "minimum": 0
                },
                "api": {
                    "type": "number",
                    "minimum": 1
                }
            }
        },
        "luna_core": {
            "type": "object",
            "properties": {
                "fsdk": {
                    "minor": {
                        "type": "number",
                        "minimum": 0
                    },
                    "major": {
                        "type": "number",
                        "minimum": 0
                    },
                    "patch": {
                        "type": "number",
                        "minimum": 0
                    },
                },
                "luna": {
                    "type": "object",
                    "properties": {
                        "minor": {
                            "type": "number",
                            "minimum": 0
                        },
                        "major": {
                            "type": "number",
                            "minimum": 0
                        },
                        "patch": {
                            "type": "number",
                            "minimum": 0
                        },
                    },
                    "api": {
                        "type": "string"
                    }
                }
            },
            "luna_api": {
                "type": "object",
                "properties": {
                    "minor": {
                        "type": "number",
                        "minimum": 0
                    },
                    "major": {
                        "type": "number",
                        "minimum": 0
                    },
                    "patch": {
                        "type": "number",
                        "minimum": 0
                    },
                    "api": {
                        "type": "number",
                        "minimum": 1
                    },
                }
            }
        }
    }
}
