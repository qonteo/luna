import graphene
from utils import call_api, urlencode_array, paginate_result, is_uuid
from graphene_objects import Account, Token, Person, PersonsPaginatedList, \
    ListQueryResult, Descriptor, DescriptorsPaginatedList, MatchCandidate, \
    CoreMatchCandidate, PersonsListsPaginatedList, DescriptorsListsPaginatedList, \
    SearchResult


class Query(graphene.ObjectType):
    """All of the defined resolve_* methods represent Graphql quieries.
    They are being called during runtime"""
    account = graphene.Field(
        Account,
        description='Get current account registration information and it\'s status.'
    )
    token = graphene.Field(
        Token,
        token_id=graphene.String(required=True, description='Token unique ID', name='uuid'),
        description='Get information about this token.'
    )
    person = graphene.Field(
        Person,
        person_id=graphene.String(description='Person unique id.', name='uuid', required=True),
        description='Get information about this person.'
    )
    persons = graphene.Field(
        PersonsPaginatedList,
        page=graphene.Int(default_value=1, description='Page number.', name='offset'),
        page_size=graphene.Int(default_value=10, description='Number of results per page.',
                               name='limit'),
        description='Get all persons owned by current account. This query is pageable.'
    )
    persons_lists = graphene.Field(
        PersonsListsPaginatedList,
        page=graphene.Int(default_value=1, description='Page number.', name='offset'),
        page_size=graphene.Int(default_value=10, description='Number of results per page.',
                               name='limit'),
        description='Get info about all persons lists owned by current account.'
    )
    descriptors_lists = graphene.Field(
        DescriptorsListsPaginatedList,
        page=graphene.Int(default_value=1, description='Page number.', name='offset'),
        page_size=graphene.Int(default_value=10, description='Number of results per page.',
                               name='limit'),
        description='Get info about all descriptors lists owned by current account.'
    )
    list_ = graphene.Field(
        ListQueryResult,
        list_id=graphene.String(name='uuid', description='List unique id.', required=True),
        page=graphene.Int(default_value=1, name='offset', description='Page number.'),
        page_size=graphene.Int(default_value=10, description='Number of results per page.',
                               name='limit'),
        name='list',
        description='Get a list. This query is pageable.'
    )
    descriptor = graphene.Field(
        Descriptor,
        descriptor_id=graphene.String(name='uuid', required=True,
                                      description='Descriptor unique id.'),
        description='Get descriptor information.'
    )
    descriptors = graphene.Field(
        DescriptorsPaginatedList,
        page=graphene.Int(default_value=1, name='offset', description='Page number.'),
        page_size=graphene.Int(default_value=10, description='Number of results per page.',
                               name='limit'),
        description='Get info about all descriptors owned '
        'by current account. This query is pageable.'
    )
    identify = graphene.Field(
        graphene.List(MatchCandidate),
        descriptor_id=graphene.String(description='The reference descriptor id.'),
        person_id=graphene.String(description='Person id to take the '
                                  'reference descriptors from.'),
        list_id=graphene.String(description='Candidates list id.'),
        person_ids=graphene.List(graphene.String,
                                 description='Comma-separated list of candidate person ids'),
        limit=graphene.Int(default_value=3,
                           description='Maximum number of similar persons to return.'),
        description='Match a descriptor or person to a list of candidate persons.'
        'Only one of descriptor_id or person_id parameters should be specified as '
        'the reference at a time. You can not set both at once. Also only one of '
        'list_id or person_ids parameters should be specified as the candidate.'
    )
    verify = graphene.Field(
        graphene.List(MatchCandidate),
        descriptor_id=graphene.String(description='The reference descriptor id.'),
        person_id=graphene.String(description='The reference person id.'),
        description='Match a descriptor to candidate person descriptors.'
    )
    match = graphene.Field(
        graphene.List(CoreMatchCandidate),
        descriptor_id=graphene.String(description='The reference descriptor id.'),
        person_id=graphene.String(description='Person id to take the '
                                  'reference descriptors from.'),
        list_id=graphene.String(description='Candidates list id.'),
        descriptor_ids=graphene.List(graphene.String,
                                     description='Comma-separated list of '
                                     'candidate descriptor ids'),
        limit=graphene.Int(default_value=3, description='Number of similar persons.'),
        description='Match a descriptor or a person to a list of candidate descriptors. '
        'Only one of descriptor_id or person_id query parameters should be specified as '
        'the reference at a time. You can not set both at once. Also only one of list_id '
        'or descriptor_ids should be specified as the candidate.'
    )
    search = graphene.Field(
        SearchResult,
        query=graphene.String(required=True, description='Either UUID or string'),
        page=graphene.Int(default_value=1, description='Page number.', name='offset'),
        page_size=graphene.Int(default_value=10, description='Number of results per page.',
                               name='limit'),
        description='Search object by string or UUID. Returns either Person, Descriptor, '
        'descriptors list or persons list if query is UUID. Returns persons_list if string.'
    )

    async def resolve_account(self, info):
        response = await call_api('account', 'get', info)
        return Account(**response)

    async def resolve_token(self, info, token_id):
        url = 'account/tokens/{}'.format(token_id)
        response = await call_api(url, 'get', info)
        return Token(id=token_id, **response)

    async def resolve_person(self, info, person_id):
        url = 'storage/persons/{}'.format(person_id)
        response = await call_api(url, 'get', info)
        return Person(**response)

    async def resolve_persons(self, info, page, page_size):
        response = await call_api(
            'storage/persons', 'get', info,
            params={'page': page, 'page_size': page_size}
        )
        return PersonsPaginatedList(**response)

    async def resolve_persons_lists(self, info, page, page_size):
        response = await call_api(
            'storage/lists', 'get', info,
            params={'page': page, 'page_size': page_size}
        )
        response['items'] = response.pop('lists', {}).pop('person_lists', {})
        response.pop('descriptors_list_count')
        return PersonsListsPaginatedList(**response)

    async def resolve_descriptors_lists(self, info, page, page_size):
        response = await call_api(
            'storage/lists', 'get', info,
            params={'page': page, 'page_size': page_size}
        )
        response['items'] = response.pop('lists', {}).pop('descriptor_lists', {})
        response.pop('persons_list_count')
        return DescriptorsListsPaginatedList(**response)

    async def resolve_list_(self, info, list_id, page, page_size):
        url = 'storage/lists/{}'.format(list_id)
        response = await call_api(
            url, 'get', info,
            params={'page': page, 'page_size': page_size}
        )
        return ListQueryResult(id=list_id, **response)

    async def resolve_descriptor(self, info, descriptor_id):
        url = 'storage/descriptors/{}'.format(descriptor_id)
        response = await call_api(url, 'get', info)
        return Descriptor(**response)

    async def resolve_descriptors(self, info, page, page_size):
        response = await call_api(
            'storage/descriptors', 'get', info,
            params={'page': page, 'page_size': page_size}
        )
        return DescriptorsPaginatedList(**response)

    async def resolve_identify(self, info, **kwargs):
        kwargs = urlencode_array(kwargs, 'person_ids')
        response = await call_api(
            'matching/identify', 'post', info,
            params=kwargs
        )
        for candidate in response['candidates']:
            candidate.pop('external_id', None)
        return [MatchCandidate(**candidate) for candidate in response['candidates']]

    async def resolve_verify(self, info, **kwargs):
        response = await call_api(
            'matching/verify', 'post', info,
            params=kwargs
        )
        for candidate in response['candidates']:
            candidate.pop('external_id', None)
        return [MatchCandidate(**candidate) for candidate in response['candidates']]

    async def resolve_match(self, info, **kwargs):
        kwargs = urlencode_array(kwargs, 'descriptor_ids')
        response = await call_api(
            'matching/match', 'post', info,
            params=kwargs
        )
        return [CoreMatchCandidate(**candidate) for candidate in response['candidates']]

    async def resolve_search(self, info, query, page, page_size):
        if not is_uuid(query):
            response = await call_api(
                'storage/persons', 'get', info,
                params={'user_data': query, 'page': page, 'page_size': page_size}
            )
            return PersonsPaginatedList(**response)

        objects = {
            'descriptors': Descriptor,
            'lists': ListQueryResult,
            'persons': Person,
        }
        search_result = None

        for url_part, model in objects.items():
            url = 'storage/{}/{}'.format(url_part, query)
            response = await call_api(url, 'get', info, ignore_errors=True)
            if not response:
                continue
            search_result = model(id=response.pop('id', query), **response)
        return search_result
