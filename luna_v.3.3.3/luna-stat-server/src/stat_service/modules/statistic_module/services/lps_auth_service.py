import asyncio
from logging import getLogger

import aiohttp

from common.api_tools import ApiError
from common.secure_cookies.cookies import decode_signed_value


log = getLogger('ss.stat_module.service.lps_auth')


class NoCredentialsError(ApiError):
    code = 400
    description = 'No credentials provided'


class WrongCredentialsError(ApiError):
    code = 400
    description = 'Wrong credentials given'


class LPSRemoteUnavailable(ApiError):
    code = 500
    description = 'LPS server "{lps_remote}" unavailable'


class UserNotAuthorized(ApiError):
    code = 401
    description = 'User credentials "{credentials}" unauthorized'


def normalise_headers(headers):
    if 'authorization' in headers:
        headers['Authorization']=headers.pop('authorization')
    if 'x-auth-token' in headers:
        headers['X-Auth-Token']=headers.pop('x-auth-token')

class LPSUserAuthService(object):
    """
    Perform authorization using LPS server
    """

    def __init__(
        self, loop: asyncio.AbstractEventLoop, lps_remote: str,
            session: aiohttp.ClientSession=None, cookie_secret=None
    ):
        self._lps_remote = lps_remote
        self._loop = loop
        self._http_session = session
        self._cookie_secret = cookie_secret

    async def check_user_authorized_by_request(self, query=None, headers=None, cookies=None):
        """
        Parse authorization data from everywhere.
        :param query: dict with {'key':'value'} query parameters
        :param headers: dict with {'key':'value'} headers
        :param cookies: dict with {'key':'value'} cookies
        :return:
        """
        if query is None:
            query = {}
        if headers is None:
            headers = {}
        if cookies is None:
            cookies = {}

        normalise_headers(headers)

        auth_token = headers.get('X-Auth-Token') or query.get('auth_token', None)
        basic_pair = headers.get('Authorization') or query.get('basic', None)
        if auth_token is None and basic_pair is None and self._cookie_secret is not None:
            basic_pair = decode_signed_value(
                self._cookie_secret, 'Authorization', cookies.get('Authorization')
            )
            if basic_pair is not None:
                basic_pair = basic_pair

        return await self.check_user_authorized(auth_token, basic_pair)

    async def check_user_authorized(self, auth_token=None, basic_pair=None):
        """
        Retrieve Account ID from the LPS server using Auth token or Basic authorization string

        :param auth_token:
        :param basic_pair:
        :return: account id

        :raise NoCredentialsError if no credentials provided
        :raise UserNotAuthorized if LPS responds with 401 status code
        :raise LPSRemoteUnavailable if connection reaches timeout or given URL is wrong
        """
        if auth_token is None and basic_pair is None:
            raise NoCredentialsError()

        headers = {}
        if auth_token is not None:
            headers['X-Auth-Token'] = auth_token
        elif basic_pair is not None:
            headers['Authorization'] = basic_pair

        if self._http_session is not None:
            return await self._request(self._http_session, auth_token, basic_pair, headers)
        else:
            async with aiohttp.ClientSession(loop=self._loop) as session:
                return await self._request(session, auth_token, basic_pair, headers)

    async def _request(self, session, auth_token, basic_pair, headers):
        log.debug(f'Checking user credentials "{auth_token or basic_pair}"')

        try:
            async with session.get(
                self._lps_remote, headers=headers
            ) as response:
                if response.status == 401:
                    log.debug(f'User with auth credentials "{auth_token or basic_pair}" unauthorized')
                    raise UserNotAuthorized(credentials=(auth_token or basic_pair))
                elif response.status == 200:
                    user_id = await response.text()
                    log.debug(
                        f'User with auth credentials "{auth_token or basic_pair}" '
                        f'has been authorized with id "{user_id}"'
                    )
                    return user_id
                else:
                    log.debug(f'Unexpected LPS answer: {response.status}')
                    raise LPSRemoteUnavailable(lps_remote=self._lps_remote)
        except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError, aiohttp.ServerTimeoutError):
            log.debug(f'LPS remote unavailable "{self._lps_remote}"')
            raise LPSRemoteUnavailable(lps_remote=self._lps_remote)
