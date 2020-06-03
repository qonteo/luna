from tests.matcher.unittests_abstract_match import TestAbstractMatching
from tests.classes import authStr
from tests import luna_api_functions



class TestMatchingComplex(TestAbstractMatching):
    """
    Tests of matching
    """

    def setUp(self):
        self.createAccountAndToken()

    def test_matching_duplicate_id(self):
        """
        .. test:: test_matching_duplicate_id

             :resources: "/matching/match,/matching/identify"
             :description: check duplicate  descriptor or person with good similarity vs person with 2 descriptors
             :LIS: No
             :tag: Match
        """
        @self.authorization
        def duplicatedIdTest(headers, auth):

            descriptorsListId = self.createList(headers, False)

            for photoId in self.dynamicDescriptorsList:
                luna_api_functions.linkListToDescriptor(headers, photoId, descriptorsListId, 'attach')

            photoId = self.createPhoto(headers)
            luna_api_functions.linkListToDescriptor(headers, photoId, descriptorsListId, 'attach')

            personId = self.createPersonWithPhoto(headers)
            descriptorId = self.createPhoto(headers)
            luna_api_functions.linkDescriptorToPerson(headers, personId, descriptorId, "attach")
            reply = luna_api_functions.match(headers, listId=descriptorsListId, personId=personId)
            self.assertTrue(reply.statusCode == 201, authStr(auth))
            self.assertSuccessMatching(reply, authStr(auth), False)
            self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))
            self.assertEqual(reply.body["candidates"][0]["similarity"], 1, authStr(auth))
            self.assertTrue(reply.body["candidates"][1]["similarity"] < 1, authStr(auth))
            ids = [res["id"] for res in reply.body["candidates"]]
            self.assertEqual(len(set(ids)), 3, authStr(auth))

            personsListId = self.createList(headers, True)

            for person in self.dynamicPersonsList:
                luna_api_functions.linkListToPerson(headers, person, personsListId, 'attach')

            luna_api_functions.linkListToPerson(headers, personId, personsListId, "attach")
            reply = luna_api_functions.identify(headers, listId=personsListId, personId=personId)
            self.assertSuccessMatching(reply, authStr(auth))
            self.assertTrue(len(reply.body["candidates"]) == 3, authStr(auth))
            self.assertEqual(reply.body["candidates"][0]["similarity"], 1, authStr(auth))
            self.assertTrue(reply.body["candidates"][1]["similarity"] < 1, authStr(auth))
            ids = [res["person_id"] for res in reply.body["candidates"]]
            self.assertEqual(len(set(ids)), 3, authStr(auth))

        duplicatedIdTest()