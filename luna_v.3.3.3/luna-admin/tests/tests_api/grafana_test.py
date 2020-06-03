from base_class import BaseClass


class TestGrafana(BaseClass):

    def test_get_grafana(self):
        response = TestGrafana.admin_client.get_grafana()
        self.assertEqual(200, response.status_code)
        self.assertIn("grafana_url", response.content)

    def test_method_not_allowed(self):
        self.methodNotAllowed("{}/grafana".format(BaseClass.admin_client.url),
                              ["post", "put", "delete", "patch"])
