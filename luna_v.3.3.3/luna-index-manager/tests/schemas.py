"""Schemas

Module contains json schemas for validating responses.
"""

uuid_pattern = "^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
TYPE_UUID4 = {"type": "string", "pattern": uuid_pattern}
TYPE_COUNT = {"type": "integer", "minimum": 0}
TYPE_NULL = {"type": "null"}

VERSION_SCHEMA = {
    "type": "object",
    "properties": {
        'Version': {
            "type": "object",

            "properties": {
                'api': {"type": "integer", "minimum": 0},
                'major': {"type": "integer", "minimum": 0},
                'minor': {"type": "integer", "minimum": 0},
                'patch': {"type": "integer", "minimum": 0},
            },

            "required": ['api', 'major', 'minor', 'patch'],
            "additionalProperties": False
        }
    },
    "required": ['Version'],
    "additionalProperties": False
}

ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "detail": {"type": "string"},
        "desc": {"type": "string"},
        "error_code": {"type": "integer"},
    },
    "required": ['detail', 'desc', "error_code"],
    "additionalProperties": False
}
