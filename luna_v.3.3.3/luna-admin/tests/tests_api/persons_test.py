from base_class import BaseClass
from schemas import PERSONS_SCHEMA


class TestPersons(BaseClass):
    person = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.person = TestPersons.employer.api_client.createPerson().body["person_id"]

    def test_get_persons(self):
        response = TestPersons.admin_client.get_persons()

        self.assertEqual(response.status_code, 200)
        self.assertSchema(response.content, PERSONS_SCHEMA)

    def test_get_persons_of_account(self):
        response = TestPersons.admin_client.get_persons({"account_id": TestPersons.employer.account_id})

        self.assertEqual(response.status_code, 200)
        self.assertSchema(response.content, PERSONS_SCHEMA)

    def test_get_persons_with_pagination(self):
        for _ in range(2):
            TestPersons.employer.api_client.createPerson()

        response = TestPersons.admin_client.get_persons({"account_id": TestPersons.employer.account_id,
                                                         "page": 1, "page_size": 2})
        self.assertSchema(response.content, PERSONS_SCHEMA)
        self.assertEqual(2, len(response.content["persons"]))
        response = TestPersons.admin_client.get_persons({"account_id": TestPersons.employer.account_id,
                                                         "page": 2, "page_size": 2})
        self.assertEqual(1, len(response.content["persons"]))

    def test_get_persons_bad_params(self):
        bad_params = {"page": "a", "page_size": "a", "account_id": "112"}
        self.badParamTests(bad_params, TestPersons.admin_client.get_persons)

    def test_method_not_allowed(self):
        self.methodNotAllowed("{}/persons".format(BaseClass.admin_client.url),
                              ["post", "put", "delete"])
