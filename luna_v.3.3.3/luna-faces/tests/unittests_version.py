from tests.classes import TestBase
from tests.shemas import SHEMA_GET_VERSION


class TestGetVersion(TestBase):
    """
    Test getVersion
    """
    def test_check_version(self):
        """
            :description: Getting the version.
            :resources: "/version"
        """
        reply = self.FacesApi.getVersion()
        self.assertEqual(reply.statusCode, 200)
        self.validateJson(reply.json, SHEMA_GET_VERSION)

    def test_version_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/version'
        """
        self.methods_test('/version', ['get'])
