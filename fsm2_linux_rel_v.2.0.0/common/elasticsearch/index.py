# todo make   "enabled":False - index ignore somewhere else

d = {"type": "date"}
o = {"type": "object"}
i = {"type": "integer"}
t = {"type": "text"}

f = {"type": "float"}
b = {"type": "boolean"}
k = {"type": "keyword"}

srsE = {
    "type": "nested",
    "properties": {
        "candidates": {
            "type": "nested",
            "properties": {
                "person_id": k,
                "similarity": f,
                "descriptor_id": k,
                "user_data": t
            }
        },
        "list_id": k,
    }
}
srsG = {
    "type": "nested",
    "properties": {
        "candidate": {
            "type": "nested",
            "properties": {
                "person_id": k,
                "similarity": f,
                "descriptor_id": k,
                "user_data": t
            }
        },
        "list_id": k,
    }
}

indexes = [
    (
        '/handlers',
        {
            "mappings": {
                "doc": {
                }
            }
        }
    ),
    (
        '/tasks',
        {
            "mappings": {
                "doc": {
                }
            }
        }
    ),
    (
        '/tasks_counter',
        {
            "mappings": {
                "doc": {
                    "properties": {
                        "count": i
                    }
                }
            }
        }
    ),
    (
        '/tasks_done',
        {
            "mappings": {
                "doc": {
                    "properties": {
                        # nested 1
                        "result": {
                            "type": "object",
                            "properties": {
                                # nested 2
                                "success": {
                                    "type": "object",
                                    "properties": {
                                        "reference": {
                                            "type": "text"
                                        },
                                        # nested 3
                                        "candidates": {
                                            "type": "object",
                                            "properties": {
                                                "id": {
                                                    "type": "text"
                                                },
                                                "similarity": {
                                                    "type": "float"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    ),
    (
        '/groups',
        {
            "mappings": {
                "doc": {
                    "properties": {
                        "search": srsG,
                        "source": t,
                        "age": i,
                        "ttl": i,
                        "person_id": k,
                        "descriptors": k,
                        "id": k,
                        "processed": b,
                        "handler_id": k,
                        "persons_lists": k,
                        "gender": f,
                        "error": o,
                        "create_time": d,
                        "external_tracks_id": t,
                        "last_update": d
                    },
                },
            }
        }
    ),
    (
        '/events',
        {
            "mappings": {
                "doc": {
                    "properties": {
                        "user_data": t,
                        "source": t,
                        "handler_id": k,
                        "group_id": k,
                        "person_id": k,
                        "external_id": t,
                        "persons_lists": k,
                        # inner object 1
                        "search_by_group": {
                            "type": "object",
                            "properties": {
                                "similarity": f,
                                "id": t
                            }
                        },
                        # inner object 2
                        "error": o,
                        "descriptors_lists": t,
                        "create_time": d,
                        # inner object 3
                        "search": srsE,
                        "warped_img": b,
                        # inner object 4
                        "extract": {
                            "type": "object",
                            "properties": {
                                # inner object 5
                                "rect": {
                                    "enabled": False,
                                    "type": "object",
                                    "properties": {
                                        "x": i,
                                        "width": i,
                                        "height": i,
                                        "y": i
                                    }
                                },
                                # inner object 6
                                "attributes": {
                                    "type": "object",
                                    "properties": {
                                        "eyeglasses": f,
                                        "gender": f,
                                        "age": f
                                    }
                                },
                                "id": t,
                                "score": f,
                                # inner object 7
                                "rectISO": {
                                    "enabled": False,
                                    "type": "object",
                                    "properties": {
                                        "x": i,
                                        "width": i,
                                        "height": i,
                                        "y": i
                                    }
                                }
                            }
                        },
                        "tags": k,
                        "id": k,
                        "descriptor_id": k,
                    }
                }
            }
        }
    )
]
