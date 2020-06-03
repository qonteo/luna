uuid_pattern = "^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$"
TYPE_UUID4 = {"type": "string", "pattern": uuid_pattern}

REEXTRACT_DESCRIPTORS_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "descriptors": {"type": "array",
                        "items": TYPE_UUID4
                        },
    },
    "required": ["descriptors"]
}
