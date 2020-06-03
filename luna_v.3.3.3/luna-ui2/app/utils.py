import re
import logging
from contextlib import contextmanager
from base64 import b64encode

import aiohttp
from aiohttp_session import get_session
from graphql import GraphQLError


@contextmanager
def supress_module_warnings(module):
    """This context manager is required to supress aiohttp_session warning
    about changed encryption key"""
    logger = logging.getLogger(module)
    default_logging_level = logger.getEffectiveLevel()
    logger.setLevel(logging.ERROR)
    yield
    logger.setLevel(default_logging_level)


def build_api_url(request, method):
    return '{}{}'.format(request.app['luna_api_uri'], method)


def encode_credentials(login, password):
    """Base64 encode user credentials for Basic HTTP Authorization"""
    encoded_credentials = '{}:{}'.format(login, password).encode()
    return b64encode(encoded_credentials).decode('utf-8')


async def build_headers(request):
    """Set authorization headers for Luna API"""
    with supress_module_warnings("aiohttp_session"):
        session = await get_session(request)

    headers = {}

    if session.get('creds'):
        headers['Authorization'] = 'Basic {}'.format(session.get('creds'))

    if session.get('x_auth'):
        headers['X-Auth-Token'] = session.get('x_auth')
    return headers


async def make_base_api_call(method, http_verb, request, headers=None,
                             ignore_errors=False, stream=False, **kwargs):
    """Call Luna API
    method - desired Luna API method
    http_verb - one of 'get', 'post', 'patch', 'delete'
    request - aiohttp.web.Request object
    headers - additional headers for request. Authorization headers are built automatically
    stream - used to download files. Set to True if response is binary
    """
    headers = headers or {}
    api_url = build_api_url(request, method)
    async with aiohttp.ClientSession() as session:
        request_call = getattr(session, http_verb)
        authorization_headers = await build_headers(request)
        headers.update(authorization_headers)
        async with request_call(api_url, headers=headers, **kwargs) as response:
            if stream:
                return await response.read()
            return response


async def call_api(method, http_verb, info, request=None, to_json=True,
                   ignore_errors=False, headers=None, **kwargs):
    """Graphene compatible call to Luna API
    method - desired Luna API method
    http_verb - one of 'get', 'post', 'patch', 'delete'
    info - info object which is being passed to every graphene resolver
    request - aiohttp.web.Request object
    to_json - whether API response should be loaded as json
    ignore_errors - set to True if you do not want raise API exceptions
    headers - additional headers for request. Authorization headers are built automatically
    """
    headers = headers or {}
    request = info.context.get('request')
    response = await make_base_api_call(method, http_verb, request, headers=headers, **kwargs)
    if response.status >= 400:
        if not ignore_errors:
            raise GraphQLError(await response.text())
        if ignore_errors and to_json:
            return {}
        return
    if to_json:
        return await response.json()


async def authorize_user(info, login=None, password=None, token=None):
    """Get user credentials and store them in an encrypted session"""
    request = info.context.get('request')
    encoded_credentials = encode_credentials(login, password)
    session = await get_session(request)
    session.clear()
    session['creds'] = encoded_credentials
    if token:
        session['x_auth'] = token
    login_data = await call_api('account', 'get', info)
    return login_data


async def paginate_result(result, limit, offset):
    """Self-implemented pagination for queries without native pagination api"""
    page_start_index = (offset - 1) * limit
    page_end_index = offset * limit
    return result[page_start_index:page_end_index]


def urlencode_array(params, *args):
    """Encode list of values to url-encoded string
    Example:
    ['Jane', 'John', 'Smith'] -> 'Jane%2CJohn%2CSmith'
    """
    for parameter in args:
        if parameter in params:
            params[parameter] = '%2C'.join(params[parameter])
    return params


def is_uuid(string):
    uuid_regexp = '^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$'
    return re.fullmatch(uuid_regexp, string)
