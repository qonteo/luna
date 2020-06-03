import sys

import base64
import random
import string
import time
from urllib.request import urljoin
from uuid import uuid4, UUID

import asyncio

import requests

import unittest

from . import AsyncTestCaseMixin  # the reason unknown, but pycharm unittest runner fails to run test, which imports from 'common' package, this is workaround
from stat_service.modules.statistic_module.services.lps_auth_service import LPSUserAuthService, NoCredentialsError, UserNotAuthorized


def _run_lps_stub(host, port, pairs, tokens):
    from multiprocessing import Process

    def _serve(host, port, pairs, tokens):
        import sys
        from uuid import UUID
        from japronto import Application

        def server_exit(request):
            def close_el():
                request.app.loop.stop()

            request.app.loop.call_soon(close_el)
            return request.Response(code=200)

        def handle_check_user_auth(request):
            basic_pair = request.headers.get('Authorization')
            auth_token = request.headers.get('X-Auth-Token')
            if basic_pair is not None:
                if not basic_pair.lower().startswith('basic '):
                    return request.Response(code=400)

                auth_base64 = basic_pair[len("Basic "):]
                auth_data = base64.b64decode(auth_base64).decode("utf-8")
                tow_dot_index = auth_data.index(":")
                login = auth_data[0:tow_dot_index]
                password = auth_data[tow_dot_index + 1:]

                if login in pairs and pairs[login] != password or login not in pairs:
                    return request.Response(code=401)

                res = str(UUID(int=(hash(password) + hash(login)) % sys.maxsize))
            elif auth_token is not None:
                try:
                    res = str(UUID(auth_token))
                    if res not in tokens:
                        return request.Response(code=401)
                except ValueError:
                    return request.Response(code=400)
            else:
                return request.Response(code=401)
            return request.Response(code=200, text=res)

        app = Application()
        app.router.add_route('/login', handle_check_user_auth, 'GET')
        app.router.add_route('/exit', server_exit, 'GET')
        app.run(host, port)

    p = Process(target=_serve, args=(host, port, pairs, tokens))
    p.start()
    time.sleep(2)
    return p


def get_base64_pair(login, password):
    return 'Basic {}'.format(
        base64.b64encode(f'{login}:{password}'.encode()).decode()
    )


def generate_random_credentials():
    return (
        ''.join(
            random.choice(string.ascii_letters)
            for _ in range(random.randint(5, 10))
        ),
        ''.join(
            random.choice(string.digits + string.ascii_letters)
            for _ in range(random.randint(6, 20))
        )
    )


class LpsAuthServiceTestCase(unittest.TestCase, AsyncTestCaseMixin):
    ACCOUNTS = {
        l: p for l, p in (
            generate_random_credentials()
            for _ in range(random.randint(10, 20))
        )
    }

    INVALID_ACCOUNTS = {
        l: p for l, p in (
            generate_random_credentials()
            for _ in range(random.randint(10, 20))
        )
    }

    TOKENS = [
        str(uuid4()) for _ in range(random.randint(10, 20))
    ]

    INVALID_TOKENS = [
        str(uuid4()) for _ in range(random.randint(10, 20))
    ]

    @classmethod
    def setUpClass(cls):
        port = 23412
        cls.auth_server = _run_lps_stub('localhost', port, cls.ACCOUNTS, cls.TOKENS)
        cls.auth_service = LPSUserAuthService(
            asyncio.get_event_loop(),
            urljoin(
                f'http://localhost:{port}', 'login'
            )
        )

    @classmethod
    def tearDownClass(cls):
        port = 23412
        requests.get(
            urljoin(
                f'http://localhost:{port}', 'exit'
            )
        )
        cls.auth_server.join()

    async def test_nope(self):
        with self.assertRaises(NoCredentialsError):
            await self.auth_service.check_user_authorized_by_request()

    async def test_basic_headers(self):
        async def rm(base_pair):
            return await self.auth_service.check_user_authorized_by_request(
                headers={'Authorization': base_pair}
            )
        await self._test_basic(rm)

    async def test_basic_query(self):
        async def rm(base_pair):
            return await self.auth_service.check_user_authorized_by_request(
                query={'basic': base_pair}
            )
        await self._test_basic(rm)

    async def test_basic_cookie(self):
        async def rm(base_pair):
            return await self.auth_service.check_user_authorized_by_request(
                cookies={'Authorization': base_pair}
            )
        await self._test_basic(rm)

    async def test_auth_token_headers(self):
        async def rm(token):
            return await self.auth_service.check_user_authorized_by_request(
                headers={'X-Auth-Token': token}
            )
        await self._test_auth_token(rm)

    async def test_auth_token_query(self):
        async def rm(token):
            return await self.auth_service.check_user_authorized_by_request(
                query={'auth_token': token}
            )
        await self._test_auth_token(rm)

    async def _test_basic(self, auth_request):
        for login, password in self.ACCOUNTS.items():
            res = await auth_request(get_base64_pair(login, password))
            self.assertEqual(
                UUID(res),
                UUID(int=(hash(login) + hash(password)) % sys.maxsize)
            )

        for login, password in self.INVALID_ACCOUNTS.items():
            with self.assertRaises(UserNotAuthorized):
                await auth_request(get_base64_pair(login, password))

    async def _test_auth_token(self, auth_request):
        for token in self.TOKENS:
            res = await auth_request(token)
            self.assertEqual(
                res, token
            )

        for token in self.INVALID_TOKENS:
            with self.assertRaises(UserNotAuthorized):
                await auth_request(token)


if __name__ == '__main__':
    import unittest
    unittest.main()
