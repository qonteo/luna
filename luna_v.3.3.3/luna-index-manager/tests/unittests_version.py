# -*- coding: utf-8 -*-
"""Version module

Tests for getting version
"""
from tests.config import SERVER_ORIGIN, SERVER_API_VERSION
from tests.base_test_class import TestBase
import requests
from tests.schemas import VERSION_SCHEMA


class VersionTest(TestBase):
    """
    Class for testing version receiving.
    """

    def test_get_version(self) -> None:
        """
        Get version.

        .. test::test_get_version

            :description: Getting the version.
            :resources: '/version'
        """
        version = requests.get("{}/version".format(SERVER_ORIGIN)).json()
        TestBase.validateJson(version, VERSION_SCHEMA)
        self.assertEqual(SERVER_API_VERSION, version["Version"]["api"])
