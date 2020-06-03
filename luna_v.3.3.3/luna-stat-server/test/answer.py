from uuid import UUID

http_date_value = '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\+-]\d{2}:\d{2}'

NoneType = type(None)

http_none = {}

http_search = {
    'columns': [
        'time',
        'age',
        'face_score',
        'gender',
        'glasses',
        'similarity',
    ],
    'values': [
        [
            http_date_value,
            NoneType,
            float,
            NoneType,
            NoneType,
            float,
        ]
    ]
}

http_extract = {
    'columns': [
        'time',
        'age',
        'face_score',
        'gender',
        'glasses',
    ],
    'values': [
        [
            http_date_value,
            NoneType,
            float,
            NoneType,
            NoneType
        ]
    ]
}

http_extract_attributes = {
    "columns": [
        'time',
        'age',
        'face_score',
        'gender',
        'glasses',
    ],
    "values": [
        [
            http_date_value,
            float,
            float,
            float,
            int
        ]
    ]
}

http_verify = {
            'columns': [
                'time',
                'age',
                'face_score',
                'gender',
                'glasses',
                'similarity',
                        ],
            'values': [
                [
                    http_date_value,
                    NoneType,
                    NoneType,
                    NoneType,
                    NoneType,
                    float,
                ]
            ]
        }

http_identify = {
            'columns': [
                'time',
                'age',
                'face_score',
                'gender',
                'glasses',
                'similarity'
            ],
            'values': [
                [
                    http_date_value,
                    NoneType,
                    NoneType,
                    NoneType,
                    NoneType,
                    float,
                ]
            ]
        }

http_match = {
            'columns': [
                'time',
                'age',
                'face_score',
                'gender',
                'glasses',
                'similarity',
            ],
            'values': [
                [
                    http_date_value,
                    NoneType,
                    NoneType,
                    NoneType,
                    NoneType,
                    float,
                ]
            ]
        }

http_any_one = {
            'columns': list,
            'values': [
                list
            ]
        }

http_any = {
            'columns': list,
            'values': list
        }

http_group_step_too_small = 'Malformed query, description: group_step is too small'

http_group_step_too_big = '400: Bad Request {"error":"error parsing query: overflowed duration 9999999w: ' \
                          'choose a smaller duration or INF"}'


http_group_step_wrong_value = 'Malformed query, description: group_step parameter has wrong value "[-\d]+[usmhdw]"'

http_time_gt_negative_timestamp = 'Malformed query, description: Type validator on tag value "time" raise: Wrong ' \
                                  'timestamp "-\d+"'

http_time_gt_wrong_value = 'Malformed query, description: time__gt parameter has wrong value "[\d-]+"'

http_error_parsing_query = '400: Bad Request {"error":"error parsing query: unable to parse integer at ' \
                           'line \d+, char \d+"}'

http_time_wrong_value = 'Malformed query, description: time__(gt)|(lt) parameter has wrong value ".*"'

ws_match = {
    'result': {
        'candidates': [
            {
                'id': UUID,
                'similarity': int
            },
            {
                'id': UUID,
                'similarity': int
            },
            {
                'id': UUID,
                'similarity': int
            },
        ]
    },
    'source': 'match',
    'event_type': 'match',
    'authorization': 'basic',
    'template': {
        'descriptor_id': UUID
    },
    'candidate': {
        'list_id': UUID,
        "list_data": str,
        "list_type": int
    },
    'timestamp': float
}

ws_extract = {
    'event_type': 'extract',
    'source': 'descriptors',
    'authorization': 'basic',
    'result': {
        'faces': [
            {
                'rect': {
                    'x': int,
                    'width': int,
                    'height': int,
                    'y': int
                },
                'score': float,
                'id': UUID,
                'rectISO': {
                    'x': int,
                    'width': int,
                    'height': int,
                    'y': int
                }
            }
        ]
    },
    'timestamp': float
}

ws_extract_token = {
    'result': {
        'faces': [
            {
                'attributes': {
                    'age': float,
                    'eyeglasses': float,
                    'gender': float,
                },
                'id': UUID,
                'rect': {
                    'height': int,
                    'width': int,
                    'x': int,
                    'y': int
                },
                'rectISO': {
                    'height': int,
                    'width': int,
                    'x': int,
                    'y': int
                },
                'score': float
            }
        ]
    },
    'source': 'descriptors',
    'event_type': 'extract',
    'authorization': {
        'token_id': UUID,
        'token_data': 'first token'
    },
    'timestamp': float
}

ws_extract_attributes = {
    'result': {
        'faces': [
            {
                'attributes': {
                    'age': float,
                    'eyeglasses': float,
                    'gender': float,
                },
                'id': UUID,
                'rect': {
                    'height': int,
                    'width': int,
                    'x': int,
                    'y': int
                },
                'rectISO': {
                    'height': int,
                    'width': int,
                    'x': int,
                    'y': int
                },
                'score': float
            }
        ]
    },
    'source': 'descriptors',
    'event_type': 'extract',
    'authorization': 'basic',
    'timestamp': float
}

ws_search = {
    "result": {
        "candidates": [
            {
                "id": UUID,
                "similarity": float
            },
            {
                "id": UUID,
                "similarity": float
            },
            {
                "id": UUID,
                "similarity": float
            },
        ],
        "face": {
            "id": UUID,
            "rect": {
                "height": int,
                "width": int,
                "x": int,
                "y": int
            },
            "rectISO": {
                "height": int,
                "width": int,
                "x": int,
                "y": int
            },
            "score": float
        }
    },
    "source": "search",
    "event_type": "match",
    "authorization": "basic",
    "template": {
        "descriptor_id": UUID
    },
    "candidate": {
        "list_id": UUID,
        "list_data": str,
        "list_type": int
    },
    "timestamp": float
}
ws_search_sim = {
    "result": {
        "candidates": [
            {
                "id": UUID,
                "similarity": float
            },
        ],
        "face": {
            "id": UUID,
            "rect": {
                "height": int,
                "width": int,
                "x": int,
                "y": int
            },
            "rectISO": {
                "height": int,
                "width": int,
                "x": int,
                "y": int
            },
            "score": float
        }
    },
    "source": "search",
    "event_type": "match",
    "authorization": "basic",
    "template": {
        "descriptor_id": UUID
    },
    "candidate": {
        "list_id": UUID,
        "list_data": str,
        "list_type": int
    },
    "timestamp": float
}

ws_identify = {}
ws_verify = {}

ws_none = NoneType
