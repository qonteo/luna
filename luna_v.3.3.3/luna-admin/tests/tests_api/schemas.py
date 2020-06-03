uuid_pattern = "^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$"
TYPE_UUID4 = {"type": "string", "pattern": uuid_pattern}
TYPE_COUNT = {"type": "integer", "minimum": 0}
TYPE_NULL = {"type": "null"}

PERSON_SHORT = {
    "type": "object",
    "properties": {
        "person_id": TYPE_UUID4,
        "account_id": TYPE_UUID4,
        "create_time": {"type": "string", "format": "date-time"},
    },
    "required": ["person_id", "account_id", "create_time"],
    "additionalProperties": False
}

PERSON_FULL = {
    "type": "object",
    "properties": {
        "person_id": TYPE_UUID4,
        "account_id": TYPE_UUID4,
        "external_id": {"anyOf": [TYPE_UUID4, TYPE_NULL]},
        "create_time": {"type": "string", "format": "date-time"},
        "faces": {"type": "array", "items": TYPE_UUID4},
        "lists": {"type": "array", "items": TYPE_UUID4},
        "user_data": {"type": "string"}

    },
    "required": ["person_id", "account_id", "create_time", "faces", "lists", "user_data"],
    "additionalProperties": False
}

DESCRIPTOR_FULL = {
    "type": "object",
    "properties": {
        "person_id": {"anyOf": [
            TYPE_UUID4,
            TYPE_NULL
        ]},
        "account_id": TYPE_UUID4,
        "face_id": TYPE_UUID4,
        "create_time": {"type": "string", "format": "date-time"},
    },
    "required": ["person_id", "account_id", "create_time", "face_id"],
    "additionalProperties": False
}

PERSONS_SCHEMA = {
    "type": "object",
    "properties": {
        "persons":
            {
                "type": "array",
                "items": PERSON_SHORT
            },
        "person_count": {"type": "integer", "minimum": 0}

    },
    "additionalProperties": False,
    "required": ["person_count", "persons"]
}

LIST_SHORT = {
    "type": "object",
    "properties": {
        "list_id": TYPE_UUID4,
        "account_id": TYPE_UUID4,
        "count_object_in_list": TYPE_COUNT,
        "last_update_time": {"type": "string", "format": "date-time"},
        "type": {
            "type": "integer",
            "enum": [0, 1]
        },
        "user_data": {"type": "string"}
    },
    "required": ["list_id", "account_id", "count_object_in_list", "last_update_time", "type", "user_data"],
    "additionalProperties": False
}


LISTS_SCHEMA = {
    "type": "object",
    "properties": {
        "lists":
            {
                "type": "array",
                "items": LIST_SHORT
            },
        "list_count": {"type": "integer", "minimum": 0}

    },
    "additionalProperties": False,
    "required": ["list_count", "lists"]
}

ACCOUNT_STATS = {
    "type": "object",
    "properties": {
        "person_count": TYPE_COUNT,
        "list_count": TYPE_COUNT,
        "token_count": TYPE_COUNT,
        "descriptor_count": TYPE_COUNT
    },
    "additionalProperties": False,
    "required": ["person_count", "list_count", "token_count", "descriptor_count"]
}
ACCOUNT_SHORT = {
    "type": "object",
    "properties": {
        "account_id": TYPE_UUID4,
        "email": {"type": "string"},
        "status": {"type": "integer",
                   "enum": [0, 1]},
        "organization_name": {"type": "string"}
    },
    "additionalProperties": False,
    "required": ["account_id", "email", "status", "organization_name"]
}

ACCOUNT_FULL = {
    "type": "object",
    "properties": {
        "stats": ACCOUNT_STATS,
        "info": ACCOUNT_SHORT
    },
    "additionalProperties": False,
    "required": ["info", "stats"]
}

ACCOUNTS_SCHEMA = {
    "type": "object",
    "properties": {
        "accounts":
            {
                "type": "array",
                "items": ACCOUNT_SHORT
            },
        "account_count": {"type": "integer", "minimum": 0}

    },
    "additionalProperties": False,
    "required": ["account_count", "accounts"]
}

TOKEN_SCHEMA = {
    "type": "object",
    "properties":
        {
            "token_id": TYPE_UUID4,
            "token_data": {"type": "string"}
        },
    "additionalProperties": False,
    "required": ["token_id", "token_data"]
}

TOKENS_SCHEMA = {
    "type": "object",
    "properties": {
        "tokens":
            {
                "type": "array",
                "items": TOKEN_SCHEMA
            },
        "token_count": {"type": "integer", "minimum": 0}

    },
    "additionalProperties": False,
    "required": ["token_count", "tokens"]
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

SEARCH_DATA = {
    "oneOf": [
        {}
    ]
}

SEARCH_SCHEMA = {
    "type": "object",
    "properties":
        {
            "data": {"oneOf": [ACCOUNT_FULL, PERSON_FULL, LIST_SHORT, DESCRIPTOR_FULL, TYPE_NULL]},
            "type": {"enum": ["account_list", "account", "face", "person", "luna_list", None]}
        },
    "required": ["type", "data"],
    "additionalProperties": False,
}

DB_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "host": {"type": "string"},
        "port": {"type": "integer"},
        "user_name": {"type": "string"},
        "db_name": {"type": "string"},
    },
    "required": ["host", "db_name", "user_name"],
    "additionalProperties": False,
}

STATISTIC_SCHEMA = {
    "type": "object",
    "properties": {
        "host": {"anyOf": [{"type": "string"}, TYPE_NULL]},
        "db_name": {"type": "string"},
        "grafana_url": {"anyOf": [{"type": "string"}, TYPE_NULL]}
    },
    "required": ["host", "db_name", "grafana_url"],
    "additionalProperties": False,
}

GC_SCHEMA = {
    "type": "object",
    "properties": {
        "ttl": {"type": "integer"},
    },
    "required": ["ttl"],
    "additionalProperties": False,
}

COMMON_SETTINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "log_level": {"enum": ["ERROR", "WARNING", "INFO", "DEBUG"]},
        "log_time": {"enum": ["LOCAL", "UTC"]},
        "connection_timeout": TYPE_COUNT,
        "request_timeout": TYPE_COUNT,
        "folders_with_log": {"type": "string"},
    },
    "required": ["log_level", "log_time", "connection_timeout", "request_timeout", "folders_with_log"],
    "additionalProperties": False,
}

LUNA_CORE_SETTINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "origin": {"type": "string"},
        "api_version": {"type": "integer"},
    },
    "required": ["origin", "api_version"],
    "additionalProperties": False,
}

ADMIN_TASKS_SERVER_SETTING_SCHEMA = {
    "type": "object",
    "properties": {
        "origin": {"type": "string"},
    },
    "required": ["origin"],
    "additionalProperties": False,
}

IMAGE_STORE_WARPS_SETTINGS = {
    "type": "object",
    "properties": {
        **LUNA_CORE_SETTINGS_SCHEMA["properties"],
        "bucket": {"type": "string"},
    },
    "required": [*LUNA_CORE_SETTINGS_SCHEMA["required"], "bucket"],
    "additionalProperties": False,
}

IMAGE_STORE_PORTRAITS_SETTINGS = {
    "type": "object",
    "properties": {
        **IMAGE_STORE_WARPS_SETTINGS["properties"],
        "save_portraits": {"type": "integer", "enum": [1, 0]},
    },
    "required": [*IMAGE_STORE_WARPS_SETTINGS["required"], "save_portraits"],
    "additionalProperties": False,
}

CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "admin_db": DB_SCHEMA,
        "luna_api_db": DB_SCHEMA,
        "statistic_db": STATISTIC_SCHEMA,
        "gc": GC_SCHEMA,
        "common": COMMON_SETTINGS_SCHEMA,
        "luna_core": LUNA_CORE_SETTINGS_SCHEMA,
        "luna_core_reextract": LUNA_CORE_SETTINGS_SCHEMA,
        "luna_faces": LUNA_CORE_SETTINGS_SCHEMA,
        "admin_tasks_server": ADMIN_TASKS_SERVER_SETTING_SCHEMA,
        "luna_image_store_warped_images": IMAGE_STORE_WARPS_SETTINGS,
        "luna_image_store_portraits": IMAGE_STORE_PORTRAITS_SETTINGS
    },
    "required": ["admin_db", "luna_api_db", "statistic_db", "gc", "common", "luna_core", "luna_core_reextract",
                 "luna_faces", "admin_tasks_server", "luna_image_store_warped_images", "luna_image_store_portraits"],
    "additionalProperties": False,
}
