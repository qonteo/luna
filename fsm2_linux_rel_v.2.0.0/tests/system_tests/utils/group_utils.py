from copy import deepcopy


def prepare_spamers_results_events(spamers_responses, _):
    return sorted([e for res in spamers_responses for e in res.json['events']], key=lambda e: e['id'])


def prepare_spamers_results_groups(spamers_responses, group_schema):
    spamers_result = [e for res in spamers_responses for e in res.json['events']]
    group_schema(
        group_id=spamers_result[0]['group_id'],
        gender=spamers_result[0]['extract']['attributes']['gender'],
        age=spamers_result[0]['extract']['attributes']['age']
    )
    return sorted([group_schema(descriptor_id=res['id']) for res in spamers_result], key=lambda e: e['descriptors'])


def prepare_ws_results_events(ws_responses):
    return sorted(ws_responses, key=lambda e: e['id'])


def prepare_ws_results_groups(ws_responses):
    return sorted(
        [
            {k: v for k, v in res.items() if k not in ('last_update', 'create_time')}
            for res in ws_responses
        ],
        key=lambda e: e['descriptors']
    )


def create_group_schema(external_tracks_ids: list, handler_id):
    schema = {
        'external_tracks_id': external_tracks_ids,
        'error': None,
        'descriptors': [],
        'id': None,
        'search': None,
        'ttl': 10,
        'source': None,
        'processed': False,
        'tags': [],
        'persons_lists': [],
        'handler_id': handler_id,
        'attributes': {'gender': None, 'age': None},
        'person_id': None,
        # 'last_update': '2017-11-22T19:00:22Z',
        # 'create_time': '2017-11-22T19:00:22Z'
    }
    kwargs_schema = {
        'descriptor_id': lambda v: schema['descriptors'].append(v),
        'group_id': lambda v: schema.update({'id': v}),
        'gender': lambda v: schema['attributes'].update({'gender': v}),
        'age': lambda v: schema['attributes'].update({'age': int(v)}),
    }

    def group_schema(**kwargs):
        for param in kwargs:
            kwargs_schema[param](kwargs[param])
        return deepcopy(schema)

    return group_schema
