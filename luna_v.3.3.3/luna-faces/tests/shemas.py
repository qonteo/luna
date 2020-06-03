uuid_pattern = "^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
TYPE_UUID4 = {"type": "string", "pattern": uuid_pattern}
TYPE_COUNT = {"type": "integer", "minimum": 0}
TYPE_NULL = {"type": "null"}
TYPE_UUID4_OR_NONE = {
    "anyOf": [
        {"type": "string", "pattern": uuid_pattern},
        {"type": "null"}
    ]
}

faceId = TYPE_UUID4
listId = TYPE_UUID4
attributesId = TYPE_UUID4
accountId = TYPE_UUID4
userData = {"type": "string", "maxLength": 128}
createTime = {'format': 'date-time'}
lastUpdateTime = {'format': 'date-time'}
eventId = TYPE_UUID4
faceCount = {"type": "integer"}
externalId = {"type": "string", "maxLength": 36}

SHEMA_GET_FACE = {
    "type": "object",

    "properties": {
        'face_id': faceId,
        'attributes_id': {"anyOf": [attributesId, TYPE_NULL]},
        'account_id': accountId,
        'user_data': userData,
        'create_time': createTime,
        'event_id': {"anyOf": [eventId, TYPE_NULL]},
        'person_id': {"anyOf": [TYPE_UUID4, TYPE_NULL]},
        'external_id': {"anyOf": [externalId, TYPE_NULL]},
        'lists': {
            "type": "array",
            'items': TYPE_UUID4,
            "minItems": 0
        }
    },
    "required": ['face_id', 'attributes_id', 'account_id', 'user_data', 'create_time', 'event_id', 'lists'],
    "additionalProperties": False
}

SHEMA_CREATE_FACE = {
    "type": "object",

    "properties": {
        'face_id': faceId,
    },
    "required": ['face_id'],
    "additionalProperties": False
}

SHEMA_GET_FACES = {
    "type": "object",

    "properties": {
        'count': TYPE_COUNT,
        'faces': {
            "type": "array",
            "items": SHEMA_GET_FACE,
            "minItems": 0,
        }
    },
    "required": ['count', 'faces'],
    "additionalProperties": False
}

SHEMA_GET_LIST = {
    "type": "object",

    "properties": {
        'faces': {
            'type': 'array',
            'items': SHEMA_GET_FACE,
            "minItems": 0
        },
        'list_id': listId,
        'user_data': userData,
        'account_id': accountId,
        'create_time': createTime,
        'last_update_time': lastUpdateTime,
        'face_count': {"type": "integer", "minimum": 0},
        'person_count': {"type": "integer", "minimum": 0},
        'type': {"enum": [0, 1]}
    },
    "required": ['faces', 'list_id', 'user_data', 'account_id', 'create_time', 'last_update_time', 'face_count',
                 'person_count', 'type'],
    "additionalProperties": False
}

SHEMA_CREATE_LIST = {
    "type": "object",

    "properties": {
        'list_id': listId,
    },
    "required": ['list_id'],
    "additionalProperties": False
}

SHEMA_LIST = {
    "type": "object",

    "properties": {
        'list_id': listId,
        'user_data': userData,
        'account_id': accountId,
        'create_time': createTime,
        'last_update_time': lastUpdateTime,
        'face_count': {"type": "integer", "minimum": 0},
        'type': {"enum": [0, 1]},
        'person_count': {"type": "integer", "minimum": 0}
    },
    "required": ['list_id', 'user_data', 'account_id', 'create_time', 'last_update_time', 'face_count', 'type',
                 'person_count'],
    "additionalProperties": False
}

SHEMA_GET_LISTS = {
    "type": "object",

    "properties": {
        'lists': {
            "type": "array",
            'items': SHEMA_LIST,
            "minItems": 0
        },
        'count': {"type": "integer", "minimum": 0},
    },
    "required": ['lists', 'count'],
    "additionalProperties": False
}

SHEMA_GET_VERSION = {
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

SHEMA_CREATE_PERSON = {
    "type": "object",

    "properties": {
        'person_id': listId,
    },
    "required": ['person_id'],
    "additionalProperties": False
}

SHEMA_PERSON = {
    "type": "object",

    "properties": {
        'person_id': listId,
        'user_data': userData,
        'account_id': accountId,
        'create_time': createTime,
        'external_id': {"anyOf": [externalId, TYPE_NULL]},
        'faces': {
            "type": "array",
            "items": TYPE_UUID4,
            "minItems": 0,
        },
        'lists': {
            "type": "array",
            'items': TYPE_UUID4,
            "minItems": 0
        }
    },
    "required": ['person_id', 'user_data', 'account_id', 'faces', 'create_time', 'external_id'],
    "additionalProperties": False
}

SCHEMA_GET_PERSONS = {
    "type": "object",

    "properties": {
        'persons': {
            "type": "array",
            'items': SHEMA_PERSON,
            "minItems": 0
        },
        'count': {"type": "integer", "minimum": 0},
    },
    "required": ['persons', 'count'],
    "additionalProperties": False
}

SCHEMA_REMOVING_FACES = {
    "type": "object",

    "properties": {
        'face_ids': {
            "type": "array",
            'items': TYPE_UUID4,
            "maxItems": 1000,
            "minItems": 1
        },
    },
    "required": ['face_ids'],
    "additionalProperties": False
}

FACE_ATTRIBUTES = {
    "type": "object",
    "required": ["face_id", "attributes_id"],
    "additionalProperties": False,
    "properties": {
        "face_id": TYPE_UUID4,
        "attributes_id": TYPE_UUID4_OR_NONE
    }
}

PERSON_ATTRIBUTES = {
    "type": "object",
    "required": ["person_id", "attributes_ids"],
    "additionalProperties": False,
    "properties": {
        "person_id": TYPE_UUID4,
        "attributes_ids": {
            "type": "array",
            "items": TYPE_UUID4
        },
    }
}

FACE_ATTRIBUTES_LIST = {
    "type": "array",
    'items': FACE_ATTRIBUTES
}

PERSON_ATTRIBUTES_LIST = {
    "type": "array",
    'items': PERSON_ATTRIBUTES
}

ATTRIBUTE_FROM_LIST = {
    "type": "object",

    "properties": {
        'attributes_id': attributesId,
        'link_key': {"type": "integer", "minimum": 0},
    },

    "required": ['attributes_id', 'link_key'],
    "additionalProperties": False
}

SCHEMA_GET_ATTRIBUTES_FROM_LIST = {
    "type": "array",
    'items': ATTRIBUTE_FROM_LIST,
    'minItems': 0,
    "additionalProperties": False
}

DELETION_FROM_LIST = {
    "type": "object",

    "properties": {
        'attributes_id': attributesId,
        'link_key': {"type": "integer", "minimum": 0},
        'unlink_key': {"type": "integer", "minimum": 0},
    },

    "required": ['attributes_id', 'link_key', 'unlink_key'],
    "additionalProperties": False
}

SCHEMA_GET_DELETIONS_FROM_LIST = {
    "type": "array",
    'items': DELETION_FROM_LIST,
    'minItems': 0,
    "additionalProperties": False
}

LIST_WITH_KEYS = {
    "type": "object",

    "properties": {
        'list_id': listId,
        'link_key': {"anyOf": [{"type": "integer", "minimum": 0}, TYPE_NULL]},
        'unlink_key': {"anyOf": [{"type": "integer", "minimum": 0}, TYPE_NULL]}
    },

    "required": ['list_id', 'link_key', 'unlink_key'],
    "additionalProperties": False
}

LISTS_WITH_KEYS = {
    "type": "array",
    'items': LIST_WITH_KEYS,
    'minItems': 0,
    "additionalProperties": False
}

SCHEMA_OPTIONS_LISTS = {
    "type": "object",

    "properties": {
        'lists': LISTS_WITH_KEYS,
    },

    "required": ['lists'],
    "additionalProperties": False
}
