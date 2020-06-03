uuid_pattern = "^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
TYPE_UUID4 = {"type": "string", "pattern": uuid_pattern}
TYPE_COUNT = {"type": "integer", "minimum": 0}
TYPE_NULL = {"type": "null"}

CREATING_FACE = {
    "type": "object",
    "properties": {
        "face_id": TYPE_UUID4
    },
    "required": ["face_id"],
    "additionalProperties": False
}

CREATE_FACE_SCHEMAS = {
    "type": "object",
    "properties": {
        "attributes_id": TYPE_UUID4,
        "event_id": TYPE_UUID4,
        "user_data": {
            "type": "string",
            "maxLength": 128
        },
        "external_id": {
            "type": "string",
            "maxLength": 36
        },
        "account_id": TYPE_UUID4,
    },
    "required": ["account_id", "attributes_id"],
    "additionalProperties": False
}

UPDATE_FACE_SCHEMAS = {
    "type": "object",
    "properties": {
        "attributes_id": TYPE_UUID4,
        "event_id": TYPE_UUID4,
        "user_data": {
            "type": "string",
            "maxLength": 128
        },
        "external_id": {
            "type": "string",
            "maxLength": 36
        }
    },
    "additionalProperties": False
}

UPDATE_PERSON_SCHEMA = {
    "type": "object",
    "properties": {
        "user_data": {
            "type": "string",
            "maxLength": 128
        },
        "external_id": {
            "type": "string",
            "maxLength": 36
        }
    },
    "additionalProperties": False,
    "minProperties": 1
}

CREATE_LIST_SCHEMAS = {
    "type": "object",
    "properties": {
        "account_id": TYPE_UUID4,
        "user_data": {
            "type": "string",
            "maxLength": 128
        },
        "type":{
            "type": "integer",
            "enum": [0, 1]
        }
    },
    "required": ["account_id", "type"],
    "additionalProperties": False
}

PATCH_LIST_USER_SCHEMA = {
    "type": "object",
    "properties": {
        "user_data": {
            "type": "string",
            "maxLength": 128
        }
    },
    "required": ["user_data"],
    "additionalProperties": False
}

GET_LISTS_WITH_KEYS_SCHEMA = {
    "type": "object",
    "properties": {
        "list_ids": {
            "type": "array",
            "items": TYPE_UUID4,
            "minItems": 1
        }
    },
    "required": ["list_ids"],
    "additionalProperties": False
}

DELETE_LISTS_SCHEMA = {
    "type": "object",
    "properties": {
        "list_ids": {
            "type": "array",
            "items": TYPE_UUID4,
            "minItems": 1
        }
    },
    "required": ["list_ids"],
    "additionalProperties": False
}

DELETE_FACES_SCHEMA = {
    "type": "object",
    "properties": {
        "face_ids": {
            "type": "array",
            "items": TYPE_UUID4,
            "minItems": 1
        }
    },
    "required": ["face_ids"],
    "additionalProperties": False
}

UPDATE_LIST_SCHEMA = {
    "oneOf":
        [{
            "type": "object",
            "properties": {

                "face_ids": {
                    "type": "array",
                    "items": TYPE_UUID4,
                    "minItems": 1
                },
                "action": {
                    "type": "string",
                    "enum": ["attach", "detach"]
                },
                "list_id": TYPE_UUID4,
            },
            "required": ["face_ids", "action", "list_id"],
            "additionalProperties": False},
            {
                "type": "object",
                "properties": {

                    "person_ids": {
                        "type": "array",
                        "items": TYPE_UUID4,
                        "minItems": 1
                    },
                    "action": {
                        "type": "string",
                        "enum": ["attach", "detach"]
                    },
                    "list_id": TYPE_UUID4,
                },
                "required": ["person_ids", "action", "list_id"],
                "additionalProperties": False}

        ]
}

CREATE_PERSON_SCHEMAS = {
    "type": "object",
    "properties": {
        "user_data": {
            "type": "string",
            "maxLength": 128
        },
        "external_id": {
            "type": "string",
            "maxLength": 36
        },
        "account_id": TYPE_UUID4
    },
    "required": ["account_id"],
    "additionalProperties": False
}

DELETE_PERSONS_SCHEMA = {
    "type": "object",
    "properties": {
        "person_ids": {
            "type": "array",
            "items": TYPE_UUID4,
            "minItems": 1
        }
    },
    "required": ["person_ids"],
    "additionalProperties": False
}

LINK_FACE_TO_PERSON_SCHEMA = {
     "type": "object",
     "properties": {

         "face_id": TYPE_UUID4,
         "action": {
             "type": "string",
             "enum": ["attach", "detach"]
         },
         "person_id": TYPE_UUID4,
     },
     "required": ["person_id", "action", "face_id"],
     "additionalProperties": False
}