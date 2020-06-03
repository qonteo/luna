import graphene
from aiohttp_session import get_session
from graphql import GraphQLError
from utils import call_api, authorize_user
from graphene_objects import Token, ListTypeEnum, Account


class RegisterAccount(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True, description='Email address')
        password = graphene.String(required=True, description='Account password')
        organization_name = graphene.String(required=True, description='Organization name')

    token = graphene.String(description='API token for client authorization')
    account = graphene.Field(Account)

    async def mutate(self, info, **kwargs):
        response = await call_api('accounts', 'post', info, json=kwargs)
        login, password = kwargs.get('email', ''), kwargs.get('password', '')
        token = response.get('token')
        login_data = await authorize_user(info, login=login, password=password, token=token)
        account = Account(**login_data)
        return RegisterAccount(**response, account=account)


class CreateToken(graphene.Mutation):
    class Arguments:
        token_data = graphene.String(description='User data about token. Arbitrary string.',
                                     required=True)

    token = graphene.Field(Token, description='API token for client authorization.')

    async def mutate(self, info, token_data):
        response = await call_api(
            'account/tokens', 'post', info,
            json={'token_data': token_data}
        )
        token = Token(token_data=token_data, id=response.get('token'))
        return CreateToken(token=token)


class UpdateToken(graphene.Mutation):
    class Arguments:
        token_id = graphene.String(required=True, description='Token unique id.')
        token_data = graphene.String(description='User data about token. Arbitrary string.',
                                     required=True)

    ok = graphene.Boolean()

    async def mutate(self, info, token_id, token_data):
        method = 'account/tokens/{}'.format(token_id)
        await call_api(method, 'patch', info, json={'token_data': token_data}, to_json=False)
        return UpdateToken(ok=True)


class RemoveTokens(graphene.Mutation):
    class Arguments:
        tokens = graphene.List(graphene.String, required=True, description='Array of tokens')

    ok = graphene.Boolean()

    async def mutate(self, info, tokens):
        await call_api(
            'account/tokens', 'delete', info,
            json={'tokens': tokens}, to_json=False
        )
        return RemoveTokens(ok=True)


class RemoveToken(graphene.Mutation):
    class Arguments:
        token_id = graphene.String(required=True, description='Token unique id.')

    ok = graphene.Boolean()

    async def mutate(self, info, token_id):
        method = 'account/tokens/{}'.format(token_id)
        await call_api(method, 'delete', info, to_json=False)
        return RemoveToken(ok=True)


class Login(graphene.Mutation):
    class Arguments:
        login = graphene.String(description='User login.')
        password = graphene.String(description='User password.')
        token = graphene.String(description='User authorization token.')

    ok = graphene.Boolean()
    email = graphene.String(required=True, description='Email address')
    organization_name = graphene.String(required=True, description='Account password')
    suspended = graphene.Boolean(description='Account status - suspended '
                                             '(true) or active (false).')

    async def mutate(self, info, **kwargs):
        if ('login' not in kwargs or 'password' not in kwargs) and 'token' not in kwargs:
            raise GraphQLError('Must provide either login and password or token')

        login_data = await authorize_user(info, **kwargs)
        return Login(ok=True, **login_data)


class Logout(graphene.Mutation):
    ok = graphene.Boolean()

    async def mutate(self, info, **kwargs):
        request = info.context.get('request')
        session = await get_session(request)
        session.clear()
        return Logout(ok=True)


class CreatePerson(graphene.Mutation):
    class Arguments:
        user_data = graphene.String(description='User data. Arbitrary string.')
        external_id = graphene.String(description='Used for integration with external systems')

    person_id = graphene.String(description='New person identifier.')
    user_data = graphene.String(description='User data. Arbitrary string.')
    external_id = graphene.String(description='Used for integration with external systems')

    async def mutate(self, info, **kwargs):
        response = await call_api(
            'storage/persons', 'post', info,
            json=kwargs
        )
        return CreatePerson(**kwargs, **response)


class UpdatePerson(graphene.Mutation):
    class Arguments:
        person_id = graphene.String(required=True, name='uuid', description='Person unique id')
        user_data = graphene.String(description='User data. Arbitrary string.')
        external_id = graphene.String(description='Used for integration with external systems')

    ok = graphene.Boolean()

    async def mutate(self, info, person_id, **kwargs):
        url = 'storage/persons/{}'.format(person_id)
        await call_api(
            url, 'patch', info, to_json=False,
            json=kwargs
        )
        return UpdatePerson(ok=True)


class DeletePerson(graphene.Mutation):
    class Arguments:
        person_id = graphene.String(required=True, name='uuid', description='Person unique id')

    ok = graphene.Boolean()

    async def mutate(self, info, person_id):
        url = 'storage/persons/{}'.format(person_id)
        await call_api(url, 'delete', info, to_json=False)
        return DeletePerson(ok=True)


class CreateList(graphene.Mutation):
    class Arguments:
        list_data = graphene.String(description='User data about list. Arbitrary string.')
        type_ = ListTypeEnum(default_value=ListTypeEnum.persons.value, name='type',
                             description='List data type - persons or descriptors')

    list_id = graphene.String()
    list_data = graphene.String()

    async def mutate(self, info, type_, list_data):
        response = await call_api(
            'storage/lists', 'post', info,
            params={'type': type_},
            json={'list_data': list_data}
        )
        return CreateList(list_data=list_data, **response)


class UpdateList(graphene.Mutation):
    class Arguments:
        list_id = graphene.String(required=True, name='uuid', description='List unique id.')
        list_data = graphene.String(description='User data about list. Arbitrary string.')

    ok = graphene.Boolean()

    async def mutate(self, info, list_id, list_data):
        url = 'storage/lists/{}'.format(list_id)
        await call_api(
            url, 'patch', info, to_json=False,
            json={'list_data': list_data}
        )
        return UpdateList(ok=True)


class DeleteLists(graphene.Mutation):
    class Arguments:
        lists = graphene.List(graphene.String, required=True,
                              description='Array of lists to delete.')

    ok = graphene.Boolean()

    async def mutate(self, info, lists):
        await call_api(
            'storage/lists', 'delete', info,
            to_json=False, json={'lists': lists}
        )
        return DeleteLists(ok=True)


class DeleteList(graphene.Mutation):
    class Arguments:
        list_id = graphene.String(required=True, name='uuid', description='List unique id.')

    ok = graphene.Boolean()

    async def mutate(self, info, list_id):
        url = 'storage/lists/{}'.format(list_id)
        await call_api(url, 'delete', info, to_json=False)
        return DeleteList(ok=True)


class AttachOrDetachListFromDescriptor(graphene.Mutation):
    class Arguments:
        descriptor_id = graphene.String(required=True, name='descriptorUUID',
                                        description='Descriptor unique id.')
        list_ids = graphene.List(graphene.String, required=True,
                                 name='listUUIDs', description='Array of list ids.')

    ok = graphene.Boolean()

    async def mutate(self, info, descriptor_id, list_ids, **kwargs):
        actions_mapping = {
            'attachListToDescriptor': 'attach',
            'detachListFromDescriptor': 'detach'
        }

        action = actions_mapping.get(info.field_name, '')

        kwargs['do'] = action
        url = 'storage/descriptors/{}/linked_lists'.format(descriptor_id)
        for list_id in list_ids:
            kwargs['list_id'] = list_id
            await call_api(
                url, 'patch', info, to_json=False,
                params=kwargs
            )
        return AttachOrDetachListFromDescriptor(ok=True)


class AttachOrDetachDescriptorToList(graphene.Mutation):
    class Arguments:
        descriptor_ids = graphene.List(
            graphene.String, required=True, name='descriptorUUIDs',
            description='Array of descriptor unique ids.'
        )
        list_id = graphene.String(required=True, name='listUUID', description='List id.')

    ok = graphene.Boolean()

    async def mutate(self, info, descriptor_ids, **kwargs):
        actions_mapping = {
            'attachDescriptorToList': 'attach',
            'detachDescriptorFromList': 'detach'
        }

        action = actions_mapping.get(info.field_name, '')

        kwargs['do'] = action
        for descriptor_id in descriptor_ids:
            url = 'storage/descriptors/{}/linked_lists'.format(descriptor_id)
            await call_api(
                url, 'patch', info, to_json=False,
                params=kwargs
            )
        return AttachOrDetachDescriptorToList(ok=True)


class AttachOrDetachDescriptorToPerson(graphene.Mutation):
    class Arguments:
        descriptor_ids = graphene.List(
            graphene.String, required=True, name='descriptorUUIDs',
            description='Array of descriptor unique ids.'
        )
        person_id = graphene.String(required=True, name='personUUID',
                                    description='Person unique id.')

    ok = graphene.Boolean()

    async def mutate(self, info, descriptor_ids, person_id, **kwargs):
        actions_mapping = {
            'attachDescriptorToPerson': 'attach',
            'detachDescriptorFromPerson': 'detach'
        }

        action = actions_mapping.get(info.field_name, '')
        kwargs['do'] = action
        url = 'storage/persons/{}/linked_descriptors'.format(person_id)
        for descriptor_id in descriptor_ids:
            kwargs['descriptor_id'] = descriptor_id
            await call_api(
                url, 'patch', info, to_json=False,
                params=kwargs
            )
        return AttachOrDetachDescriptorToPerson(ok=True)


class AttachOrDetachListToPerson(graphene.Mutation):
    class Arguments:
        list_ids = graphene.List(
            graphene.String, required=True, name='listUUIDs', description='Array of list ids.'
        )
        person_id = graphene.String(required=True, name='personUUID',
                                    description='Person unique id.')

    ok = graphene.Boolean()

    async def mutate(self, info, person_id, list_ids, **kwargs):
        actions_mapping = {
            'attachListToPerson': 'attach',
            'detachListFromPerson': 'detach'
        }

        action = actions_mapping.get(info.field_name, '')
        kwargs['do'] = action
        url = 'storage/persons/{}/linked_lists'.format(person_id)
        for list_id in list_ids:
            kwargs['list_id'] = list_id
            await call_api(
                url, 'patch', info, to_json=False,
                params=kwargs
            )
        return AttachOrDetachListToPerson(ok=True)


class AttachOrDetachPersonFromList(graphene.Mutation):
    class Arguments:
        list_id = graphene.String(required=True, name='listUUID', description='List id.')
        person_ids = graphene.List(
            graphene.String, required=True, name='personUUIDs',
            description='Array of person unique ids.'
        )

    ok = graphene.Boolean()

    async def mutate(self, info, person_ids, **kwargs):
        actions_mapping = {
            'attachPersonToList': 'attach',
            'detachPersonFromList': 'detach'
        }

        action = actions_mapping.get(info.field_name, '')
        kwargs['do'] = action
        for person_id in person_ids:
            url = 'storage/persons/{}/linked_lists'.format(person_id)
            await call_api(
                url, 'patch', info, to_json=False,
                params=kwargs
            )
        return AttachOrDetachPersonFromList(ok=True)


class Mutations(graphene.ObjectType):
    register_account = RegisterAccount.Field(
        description='Create a new account with given credentials. '
        'Automatically creates one API token for client authorization.'
    )
    create_token = CreateToken.Field(
        description='Create an authorization token for current account.'
    )
    update_token = UpdateToken.Field(
        description='Change token data associated with this token.'
    )
    remove_token = RemoveToken.Field(description='Delete a token.')
    remove_tokens = RemoveTokens.Field(
        description='Delete one or several authorization tokens from current account.'
    )
    create_person = CreatePerson.Field(
        description='Create a person. Optional user data may be specified.'
    )
    update_person = UpdatePerson.Field(
        description='Change user data associated with this person.'
    )
    delete_person = DeletePerson.Field(
        description='Delete a person. This also detaches all attached descriptors setting '
        'their TTL to default value. If not attached to a person or to a list, '
        'these descriptors will be eventually garbage-collected'
    )
    create_list = CreateList.Field(description='Create a list.')
    update_list = UpdateList.Field(description='Change list data associated with this list.')
    delete_list = DeleteList.Field(description='Delete a list.')
    delete_lists = DeleteLists.Field(description='Delete one or multiple lists.')
    attach_list_to_descriptor = AttachOrDetachListFromDescriptor.Field(
        description='Attach array of lists to a descriptor.'
    )
    detach_list_from_descriptor = AttachOrDetachListFromDescriptor.Field(
        description='Detach array of lists from the descriptor. Once detached, '
        'descriptor\'s TTL is reset to the default value. If not attached to a person '
        'or to a list, this descriptor will be eventually garbage-collected.'
    )
    attach_descriptor_to_list = AttachOrDetachDescriptorToList.Field(
        description='Attach array of descriptors to a list.'
    )
    detach_descriptor_from_list = AttachOrDetachDescriptorToList.Field(
        description='Detach array of descriptors from the list. Once detached, '
        'descriptor\'s TTL is reset to the default value. If not attached to a person '
        'or to a list,this descriptor will be eventually garbage-collected.'
    )
    attach_descriptor_to_person = AttachOrDetachDescriptorToPerson.Field(
        description='Attach array of descriptors to a person.'
    )
    detach_descriptor_from_person = AttachOrDetachDescriptorToPerson.Field(
        description='Detach array of descriptors from the person. Once detached, '
        'descriptor\'s TTL is reset to the default value. If not attached to a person '
        'or to a list,this descriptor will be eventually garbage-collected.'
    )
    attach_list_to_person = AttachOrDetachListToPerson.Field(
        description='Attach array of lists to a person.'
    )
    detach_list_from_person = AttachOrDetachListToPerson.Field(
        description='Detach array of lists from person.'
    )
    attach_person_to_list = AttachOrDetachPersonFromList.Field(
        description='Attach array of persons to a list.'
    )
    detach_person_from_list = AttachOrDetachPersonFromList.Field(
        description='Detach array of persons from the list.'
    )
    login = Login.Field(description='Authorize user.')
    logout = Logout.Field(description='Deauthorize user.')
