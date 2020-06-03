from base_class import BaseClass
from resources.resources import warp
from schemas import LIST_SHORT
from luna_admin.crutches_on_wheels.errors.errors import Error
from uuid import uuid4


class TestList(BaseClass):

    def test_get_list(self):
        descriptor_id = TestList.employer.api_client.extractDescriptors(
            filename=warp,
            warpedImage=True, raiseError=True).body["faces"][0]["id"]
        list_id = TestList.employer.api_client.createList(listType="descriptors", raiseError=True).body["list_id"]
        TestList.employer.api_client.linkListToDescriptor(descriptor_id, list_id, raiseError=True)
        response = TestList.admin_client.get_list(list_id)
        self.assertEqual(200, response.status_code)
        self.assertSchema(response.content, LIST_SHORT)

    def test_get_non_exist_list(self):
        response = TestList.admin_client.get_list(str(uuid4()))
        self.assertErrorRestAnswer(response, 404, Error.AccountListNotFound)

    def test_method_not_allowed(self):
        self.methodNotAllowed("{}/lists/{}".format(BaseClass.admin_client.url, str(uuid4())),
                              ["post", "put", "delete", "patch"])
