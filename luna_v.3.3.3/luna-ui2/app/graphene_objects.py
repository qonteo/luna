import arrow
import graphene
from utils import call_api, paginate_result


class Token(graphene.ObjectType):
    class Meta:
        description = 'API token for client authorization'

    id = graphene.UUID(description='UUID4', name='uuid')
    token_data = graphene.String(description='User data about token. Arbitrary string.')


class TokensPaginatedList(graphene.ObjectType):
    class Meta:
        description = 'List of user authorization tokens'

    count = graphene.Int(description='Count object in list')
    tokens = graphene.List(Token, description='List of tokens', name='items')

    async def resolve_tokens(self, info):
        return [Token(**token) for token in self.tokens]


class Account(graphene.ObjectType):
    email = graphene.String(description='Email address.')
    organization_name = graphene.String(description='Organization name.')
    suspended = graphene.Boolean(description='Account status - suspended '
                                             '(true) or active (false).')
    tokens = graphene.Field(TokensPaginatedList,
                            offset=graphene.Int(description='Page number.', default_value=1),
                            limit=graphene.Int(description='Number of results per page.',
                                               default_value=10),
                            description='All authorization tokens owned by current account.')

    class Meta:
        description = 'Account registration information and it\'s status.'

    async def resolve_tokens(self, info, offset, limit):
        response = await call_api(
            'account/tokens', 'get', info,
            params={'page': offset, 'page_size': limit}
        )
        return TokensPaginatedList(**response)


class ListTypeEnum(graphene.Enum):
    persons = 'persons'
    descriptors = 'descriptors'

    class Meta:
        description = 'Enum for list types. It can be either persons list or descriptors list'


class ListObject(graphene.ObjectType):
    id = graphene.UUID(name='uuid', description='List ID.')
    count = graphene.Int(description='Count object in list')
    list_data = graphene.String(description='User data about list. Arbitrary string.')


class Person(graphene.ObjectType):
    id = graphene.UUID(description='Person identifier.', name='uuid')
    user_data = graphene.String(description='User data about person. Arbitrary string.')
    create_time = graphene.String(date_format=graphene.String(
                                  name='format', description='Output date format'),
                                  description='Date and time when the person was created.')
    descriptors = graphene.List(lambda: Descriptor,
                                offset=graphene.Int(description='Page number.',
                                                    default_value=1),
                                limit=graphene.Int(description='Number of results per page.',
                                                   default_value=10),
                                description='List of all descriptors attached to the person')
    lists = graphene.List(ListObject, description='Array of all lists to which this person '
                                                  'is attached.')
    portrait = graphene.String(description='Portrait image corresponding to this person.')
    descriptors_count = graphene.Int(description='Count of descriptors attached to the person')
    external_id = graphene.String(description='Used for integration with external systems')

    class Meta:
        description = 'Object describing Person'

    async def resolve_descriptors(self, info, limit, offset):
        descriptors = []
        for descriptor in self.descriptors:
            response = await call_api('storage/descriptors/{}'.format(descriptor), 'get', info)
            descriptors.append(response)
        descriptors = await paginate_result(descriptors, limit, offset)
        return [Descriptor(**descriptor) for descriptor in descriptors]

    async def resolve_create_time(self, info, date_format='DD.MM.YYYY'):
        create_time = self.create_time
        if create_time:
            create_time = arrow.get(create_time).format(date_format)
        return create_time

    async def resolve_lists(self, info):
        lists = []
        response = await call_api('storage/lists', 'get', info)
        for list_ in response.get('lists', {}).get('person_lists', []):
            if list_.get('id') not in self.lists:
                continue
            lists.append(list_)
        return [ListObject(**list_) for list_ in lists]

    async def resolve_portrait(self, info):
        if self.descriptors:
            return '/portrait/{descriptor_id}'.format(descriptor_id=self.descriptors[0])

    async def resolve_descriptors_count(self, info):
        return len(self.descriptors)


class PersonsPaginatedList(graphene.ObjectType):
    persons = graphene.List(Person, name='items', description='List of persons.')
    count = graphene.Int(description='Persons count.')

    class Meta:
        description = 'Paginated list with all persons owned by current account.'

    async def resolve_persons(self, info):
        return [Person(**person) for person in self.persons]


class Descriptor(graphene.ObjectType):
    id = graphene.UUID(name='uuid', description='Descriptor identifier.')
    last_update = graphene.String(date_format=graphene.String(
                                  name='format', description='Output date format'),
                                  description='Last update date and time. Initially '
                                  'will contain descriptor creation time. Once attached '
                                  'or detached, this value is updated with operation '
                                  'timestamp.')
    person_id = graphene.Field(lambda: Person, name='person',
                               description='Person id (if attached to a person).')
    lists = graphene.List(ListObject,
                          offset=graphene.Int(description='Page number.',
                                              default_value=1),
                          limit=graphene.Int(description='Number of results per page.',
                                             default_value=10),
                          description='Array of all lists to which this '
                                      'descriptor is attached.')
    portrait = graphene.String(description='Portrait image corresponding to this descriptor.')

    class Meta:
        description = 'An object describing descriptor.'

    async def resolve_person_id(self, info):
        url = 'storage/persons/{}'.format(self.person_id)
        response = await call_api(url, 'get', info, ignore_errors=True)
        if response:
            return Person(**response)

    async def resolve_last_update(self, info, date_format='DD.MM.YYYY'):
        last_update = self.last_update
        if last_update:
            last_update = arrow.get(last_update).format(date_format)
        return last_update

    async def resolve_lists(self, info, limit, offset):
        lists = []
        response = await call_api('storage/lists', 'get', info)
        for list_ in response.get('lists', {}).get('descriptor_lists', []):
            if list_.get('id') not in self.lists:
                continue
            lists.append(list_)
        lists = await paginate_result(lists, limit, offset)
        return [ListObject(**list_) for list_ in lists]

    async def resolve_portrait(self, info):
        if self.id:
            return '/portrait/{descriptor_id}'.format(descriptor_id=self.id)


class PersonsListObject(ListObject):
    items = graphene.List(Person,
                          offset=graphene.Int(description='Page number.',
                                              default_value=1),
                          limit=graphene.Int(description='Number of results per page.',
                                             default_value=10),
                          description='List of persons.')

    async def resolve_items(self, info, limit, offset):
        response = await call_api('storage/lists/{}'.format(self.id), 'get', info)
        response['persons'] = await paginate_result(response.get('persons', []), limit, offset)
        return [Person(**person) for person in response.get('persons')]


class PersonsListsPaginatedList(graphene.ObjectType):
    persons_list_count = graphene.Int(description='Count object in list', name='count')
    items = graphene.List(PersonsListObject, description='An array of persons lists')

    class Meta:
        description = 'An object describing lists paginated query'

    async def resolve_items(self, info):
        return [PersonsListObject(**list_) for list_ in self.items]


class DescriptorsListObject(ListObject):
    id = graphene.UUID(name='uuid', description='List ID.')
    items = graphene.List(Descriptor,
                          offset=graphene.Int(description='Page number.',
                                              default_value=1),
                          limit=graphene.Int(description='Number of results per page.',
                                             default_value=10),
                          description='List of descriptors.')

    async def resolve_items(self, info, limit, offset):
        response = await call_api('storage/lists/{}'.format(self.id), 'get', info)
        descriptors = response.get('descriptors', [])
        descriptors = await paginate_result(descriptors, limit, offset)
        return [Descriptor(**descriptor) for descriptor in descriptors]


class DescriptorsListsPaginatedList(graphene.ObjectType):
    descriptors_list_count = graphene.Int(description='Count object in list', name='count')
    items = graphene.List(DescriptorsListObject, description='An array of descriptors lists')

    class Meta:
        description = 'An object describing lists paginated query'

    async def resolve_items(self, info):
        return [DescriptorsListObject(**list_) for list_ in self.items]


class DescriptorsPaginatedList(graphene.ObjectType):
    descriptors = graphene.List(Descriptor, name='items', description='List of descriptors.')
    count = graphene.Int(description='Descriptors count.')

    async def resolve_descriptors(self, info):
        return [Descriptor(**descriptor) for descriptor in self.descriptors]


class ListQueryResult(graphene.ObjectType):
    id = graphene.String(description='List unique ID.', name='uuid')
    persons = graphene.List(Person,
                            offset=graphene.Int(description='Page number.',
                                                default_value=1),
                            limit=graphene.Int(description='Number of results per page.',
                                               default_value=10),
                            description='List of persons.')
    descriptors = graphene.List(Descriptor,
                                offset=graphene.Int(description='Page number.',
                                                    default_value=1),
                                limit=graphene.Int(description='Number of results per page.',
                                                   default_value=10),
                                description='List of descriptors.')
    list_data = graphene.String(description='User data about list. Arbitrary string.')
    count = graphene.Int(description='Descriptors count.')

    class Meta:
        description = 'An object describing list query result'

    async def resolve_persons(self, info, limit, offset):
        if self.persons:
            self.persons = await paginate_result(self.persons, limit, offset)
            return [Person(**person) for person in self.persons]

    async def resolve_descriptors(self, info, limit, offset):
        if self.descriptors:
            self.descriptors = await paginate_result(self.descriptors, limit, offset)
            return [Descriptor(**descriptor) for descriptor in self.descriptors]


class MatchCandidate(graphene.ObjectType):
    similarity = graphene.Float(description='Similarity with the reference descriptor.')
    person_id = graphene.Field(Person, name='person', description='Matched person.')
    user_data = graphene.String(description='Matched person user data.')
    descriptor_id = graphene.Field(Descriptor, name='descriptor',
                                   description='Matched descriptor.')

    class Meta:
        description = 'An object describing a matching result.'

    async def resolve_person_id(self, info):
        if self.person_id:
            response = await call_api('storage/persons/{}'.format(self.person_id), 'get', info)
            if response:
                return Person(**response)

    async def resolve_descriptor_id(self, info):
        if self.descriptor_id:
            response = await call_api(
                'storage/descriptors/{}'.format(self.descriptor_id), 'get', info
            )
            if response:
                return Descriptor(**response)


class CoreMatchCandidate(graphene.ObjectType):
    id = graphene.Field(Descriptor, name='descriptor',
                        description='Matched descriptor')
    similarity = graphene.Float(description='Similarity with the reference descriptor.')

    class Meta:
        description = 'An object describing a matching result.'

    async def resolve_id(self, info):
        if self.id:
            response = await call_api(
                'storage/descriptors/{}'.format(self.id), 'get', info
            )
            if response:
                return Descriptor(**response)


class SearchResult(graphene.Union):
    class Meta:
        types = (Person, Descriptor, ListQueryResult, PersonsPaginatedList)
