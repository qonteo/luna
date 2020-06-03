from utils import make_base_api_call


async def get_person_description_from_file_name(descriptor_data, enumerated=False, count=None):
    *_, descriptor_name = descriptor_data.get('file_name').split('/')
    person_data = descriptor_name.split('.')
    person_data.pop()
    person_data = '.'.join(person_data)

    if enumerated:
        person_data = '{}_{}'.format(person_data, count)
    return person_data


async def create_person(request, person_data):
    person_response = await make_base_api_call(
        'storage/persons', 'post', request,
        json={'user_data': person_data}
    )
    person_data = await person_response.json()
    return person_data.get('person_id')


async def link_descriptor_to_person(request, person_id, descriptor_id):
    link_descriptor_api_url = 'storage/persons/{}/linked_descriptors'.format(person_id)
    await make_base_api_call(
        link_descriptor_api_url, 'patch', request,
        params={'do': 'attach', 'descriptor_id': descriptor_id}
    )


async def get_person(request, person_id):
    person_api_url = 'storage/persons/{}'.format(person_id)
    person_response = await make_base_api_call(person_api_url, 'get', request)
    return await person_response.json()
