import unittest
from tests import luna_api_functions


class TestVersion(unittest.TestCase):
    """
    test version
    """
    def test_check_version(self):
        """

        .. test:: test_check_version

            :description: Getting the version.
            :resources: "/version"
            :LIS: No
        """
        reply = luna_api_functions.getVersion()
        self.assertEqual(reply.statusCode, 200)
        self.assertTrue("Version" in reply.body)
        ver = reply.body["Version"]

        self.assertTrue("luna_api" in ver)
        self.assertTrue("luna_core" in ver)
        self.checkStandartVersion(ver["luna_api"])
        self.assertTrue("api" in ver["luna_api"])
        self.assertTrue(int(ver["luna_api"]["api"]) >= 0)

        lunaCore = ver["luna_core"]
        self.assertTrue("fsdk" in lunaCore)
        self.assertTrue("luna" in lunaCore)
        self.checkStandartVersion(lunaCore["fsdk"])
        self.checkStandartVersion(lunaCore["luna"])
        self.assertTrue("api" in lunaCore)
        self.assertTrue(int(lunaCore["api"]) >= 0)

    def checkStandartVersion(self, dictWithVersion):
        self.assertTrue("major" in dictWithVersion)
        self.assertTrue("minor" in dictWithVersion)
        self.assertTrue("patch" in dictWithVersion)
        self.assertTrue(int(dictWithVersion["major"]) >= 0)
        self.assertTrue(int(dictWithVersion["minor"]) >= 0)
        self.assertTrue(int(dictWithVersion["patch"]) >= 0)
