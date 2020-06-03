from base_class import BaseClass
from resources.resources import warp
from schemas import PERSON_FULL
from uuid import uuid4
from luna_admin.crutches_on_wheels.errors.errors import Error


class TestPerson(BaseClass):

    def test_get_person(self):
        person_id = TestPerson.employer.api_client.createPerson(raiseError = True).body["person_id"]
        list_id = TestPerson.employer.api_client.createList(listType = "persons", raiseError = True).body["list_id"]
        TestPerson.employer.api_client.linkListToPerson(person_id, list_id, raiseError = True)
        descriptor_id = TestPerson.employer.api_client.extractDescriptors(
            filename = warp,
            warpedImage = True, raiseError = True).body["faces"][0]["id"]
        TestPerson.employer.api_client.linkDescriptorToPerson(person_id, descriptor_id, raiseError = True)
        response = TestPerson.admin_client.get_person(person_id)
        self.assertEqual(200, response.status_code)
        self.assertSchema(response.content, PERSON_FULL)
        self.assertEqual(1, len(response.content["faces"]))
        self.assertEqual(descriptor_id, response.content["faces"][0])
        self.assertEqual(1, len(response.content["lists"]))
        self.assertEqual(list_id, response.content["lists"][0])

    def test_get_non_exist_person(self):
        response = TestPerson.admin_client.get_person(str(uuid4()))
        self.assertErrorRestAnswer(response, 404, Error.PersonNotFound)

    def test_method_not_allowed(self):
        self.methodNotAllowed("{}/persons/{}".format(BaseClass.admin_client.url, str(uuid4())),
                              ["post", "put", "delete", "patch"])