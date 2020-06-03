from jsonschema import validate

from tests.system_tests import base_test_class
from tests.system_tests.config import FSM2_API_VERSION
from tests.system_tests.fsmRequests import getVersion
from tests.system_tests.shemas import VERSIONSCHEMA


class TestVersion(base_test_class.BaseTest):
    def test_version(self):
        reply = getVersion()
        self.assertEqual(200, reply.statusCode, "Wrong reply.status code")
        self.assertIsNone(validate(reply.json, VERSIONSCHEMA), "Wrong version format")
        self.assertEqual(FSM2_API_VERSION, reply.json['facestreammanager2']['api'], "Wrong api version in test config")
