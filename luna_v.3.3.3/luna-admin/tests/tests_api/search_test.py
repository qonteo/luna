import uuid

from base_class import BaseClass
from resources.resources import warp
from schemas import SEARCH_SCHEMA, ACCOUNT_FULL, DESCRIPTOR_FULL, LIST_SHORT, PERSON_FULL


class TestSearch(BaseClass):
    person_id = None
    account_list_id = None
    descriptor_id = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.person_id = TestSearch.employer.api_client.createPerson(raiseError = True).body["person_id"]
        cls.account_list_id = \
        TestSearch.employer.api_client.createList(listType = "descriptors", raiseError = True).body["list_id"]
        cls.descriptor_id = TestSearch.employer.api_client.extractDescriptors(
            filename = warp,
            warpedImage = True, raiseError = True).body["faces"][0]["id"]
        TestSearch.employer.api_client.linkListToDescriptor(cls.descriptor_id, cls.account_list_id, raiseError = True)

    def assertSearchResult(self, result, objectType, objectSchema):
        self.assertSchema(result, SEARCH_SCHEMA)
        self.assertSchema(result["data"], objectSchema)
        self.assertEqual(result["type"], objectType)

    def test_search(self):
        objects = [{"type": "account", "schema": ACCOUNT_FULL, "id": TestSearch.employer.account_id},
                   {"type": "person", "schema": PERSON_FULL, "id": TestSearch.person_id},
                   {"type": "face", "schema": DESCRIPTOR_FULL, "id": TestSearch.descriptor_id},
                   {"type": "account_list", "schema": LIST_SHORT, "id": TestSearch.account_list_id}]

        for objectForSearch in objects:
            with self.subTest(type = objectForSearch["type"]):
                response = TestSearch.admin_client.search({"q": objectForSearch["id"]})
                self.assertSearchResult(response.content, objectForSearch["type"], objectForSearch["schema"])

    def test_search_account_by_email(self):
        response = TestSearch.admin_client.search({"q": TestSearch.employer.email})
        self.assertSearchResult(response.content, "account", ACCOUNT_FULL)

    def test_search_account_by_token_id(self):
        response = TestSearch.admin_client.search(
            {"q": TestSearch.employer.api_client.getTokens(raiseError = True).body["tokens"][0]["id"]})
        self.assertSearchResult(response.content, "account", ACCOUNT_FULL)

    def test_search_non_exist_object(self):
        params = [str(uuid.uuid4()), "fake@email.ru"]
        for param in params:
            response = TestSearch.admin_client.search({"q": param})
            self.assertSchema(response.content, SEARCH_SCHEMA)
            self.assertEqual(None, response.content["data"])
            self.assertEqual(None, response.content["type"])

    def test_method_not_allowed(self):
        self.methodNotAllowed("{}/search".format(BaseClass.admin_client.url),
                              ["post", "put", "delete", "patch"])
