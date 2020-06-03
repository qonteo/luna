from tests.base_class import BaseClass


class TestVersion(BaseClass):

    def tests_get_version(self):
        reply = self.StoreApi.getVersion()
        self.assertEqual(200, reply.statusCode)
        version = reply.json["Version"]
        for key in ["api", "minor", "major", "patch"]:
            self.assertTrue(type(version[key]) == int)
            self.assertTrue(version[key] >= 0)