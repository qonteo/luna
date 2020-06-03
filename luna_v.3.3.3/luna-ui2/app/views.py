import os
import json

from aiohttp import web, hdrs
from utils import make_base_api_call
from settings import ACCEPTED_INPUT_FILES, INDEX_PAGE_PATH, STATIC_ROOT
from views_helpers import get_person_description_from_file_name, create_person, \
    get_person, link_descriptor_to_person


async def extract_descriptor(request):
    if request.content.at_eof():
        return web.json_response({'detail': 'Missing file to upload'},
                                 status=400)
    reader = await request.multipart()
    field = await reader.next()

    if not field:
        return web.json_response({'detail': 'File field exhausted'},
                                 status=204)

    filename = field.filename
    content_type = field.headers.get(hdrs.CONTENT_TYPE, '')
    if content_type not in ACCEPTED_INPUT_FILES:
        return web.json_response({'detail': 'Bad/unsupported message content type'},
                                 status=415)

    image = await field.read()
    response = await make_base_api_call(
        'storage/descriptors', 'post', request,
        params=request.query, data=image,
        headers={'content-type': content_type}
    )
    api_response = await response.json()
    api_response['file_name'] = filename
    return web.json_response(api_response, status=response.status)


async def bulk_extract(request):
    """Create descriptors from multiple images,
    create person for each descriptor and link them"""
    persons = []
    errors = []
    while not request.content.at_eof():
        response = await extract_descriptor(request)
        descriptor_data = json.loads(response.text)

        if response.status == 204:
            break
        if response.status >= 400:
            errors.append(descriptor_data)
            continue

        created_descriptors = descriptor_data.get('faces', [{}])
        for count, descriptor in enumerate(created_descriptors, start=1):
            has_multiple_descriptors_from_single_image = len(created_descriptors) > 1
            descriptor_id = descriptor.get('id')

            if not descriptor_id:
                errors.append(descriptor_data)
                continue

            person_data = await get_person_description_from_file_name(
                descriptor_data, has_multiple_descriptors_from_single_image, count
            )
            person_id = await create_person(request, person_data)

            if not person_id:
                errors.append(person_data)
                continue

            await link_descriptor_to_person(request, person_id, descriptor_id)
            person = await get_person(request, person_id)
            person['portrait'] = '/portrait/{descriptor_id}'.format(
                descriptor_id=descriptor_id
            )
            person['descriptors'] = [descriptor]
            persons.append(person)
    return web.json_response({'persons': persons, 'errors': errors})


async def proxy_portrait_image(request):
    descriptor_id = request.match_info.get('descriptor_id')
    if not descriptor_id:
        return web.json_response({'detail': 'Missing descriptor id'}, status=400)
    url = 'storage/portraits/{}'.format(descriptor_id)
    response = await make_base_api_call(url, 'get', request, stream=True)
    return web.Response(body=response, content_type='image/jpeg')


async def serve_static(request):
        static_path = request.path.lstrip('/')
        if 'static' in request.path:
            *_, separator, path = request.path.partition('static')
            static_path = ''.join([separator, path])
        static_path = os.path.join(STATIC_ROOT, static_path)
        if os.path.exists(static_path):
            return web.FileResponse(static_path)
        raise web.HTTPNotFound()


async def show_index(request):
    """Serve index.html which is an entrypoint for frontend application"""
    return web.FileResponse(INDEX_PAGE_PATH)


async def handle_404(request, response):
    """Ensure that nonexistent routes are handled by frontend"""
    return await show_index(request)
