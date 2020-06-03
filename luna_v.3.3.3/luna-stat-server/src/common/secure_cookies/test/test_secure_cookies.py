import string
import uuid
import random
import unittest

import itertools
from tornado.web import create_signed_value as t_create_signed_value, decode_signed_value as t_decode_signed_value
from common.secure_cookies.cookies import create_signed_value, decode_signed_value


class TestTornadoCapability(unittest.TestCase):
    SECRETS = [
        str(uuid.uuid4()), str(uuid.uuid4()),
    ] + list(
        itertools.chain.from_iterable(
            [
                ''.join(
                    random.choice(string.printable)
                    for __ in range(l)
                )
                for l in range(random.randint(10, 60))
            ] for _ in range(random.randint(5, 10))
        )
    )

    def test_cookies(self):
        for version in (1, 2):
            for secret in self.SECRETS:
                s = create_signed_value(
                    secret, 'simple_key', 'some value', version
                )
                ts = t_create_signed_value(
                    secret, 'simple_key', 'some value', version
                )

                self.assertEqual(s, ts)

                s, ts = ts, s

                ds = decode_signed_value(secret, 'simple_key', s)
                tds = t_decode_signed_value(secret, 'simple_key', ts)

                self.assertEqual(ds, tds)
