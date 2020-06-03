from base_class import BaseClass
from schemas import CONFIG_SCHEMA


class TestConfig(BaseClass):

    def test_get_config(self):
        response = TestConfig.admin_client.get_config()
        self.assertEqual(200, response.status_code)
        self.assertSchema(response.content, CONFIG_SCHEMA)

    def test_method_not_allowed(self):
        self.methodNotAllowed("{}/config".format(BaseClass.admin_client.url),
                              ["post", "put", "delete", "patch"])
