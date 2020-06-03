from tests.classes import TestBase
from uuid import uuid4
from luna_faces.crutches_on_wheels.errors.errors import Error
import copy

DEFAULT_FACES_COUNT = 3


class TestLinker(TestBase):
    """
    Test Linker
    """

    def setUp(self):
        TestBase.setUp(self)
        self.faceListId = self.FacesApi.createList(self.account_id, raiseError=True).json['list_id']
        self.lists.append(self.faceListId)
        self.personListId = self.FacesApi.createList(self.account_id, listType=1, raiseError=True).json['list_id']
        self.lists.append(self.personListId)

        self.faceIds = []
        self.personIds = []
        for _ in range(DEFAULT_FACES_COUNT):
            faceId = self.FacesApi.createFace(self.account_id, attributesId=str(uuid4()), raiseError=True).json['face_id']
            self.faceIds.append(faceId)
            self.faces.append(faceId)
            personId = self.FacesApi.createPerson(self.account_id, raiseError=True).json['person_id']
            self.personIds.append(personId)
            self.persons.append(personId)

        self.cases = [{"params": {"personIds": self.personIds}, "list": self.personListId, "type": "persons"},
                      {"params": {"faceIds": self.faceIds}, "list": self.faceListId, "type": "faces"}]

    def badCaseSubTestWrap(self, func):
        def subTestWrap(cases):
            for case in cases:
                with self.subTest(listType=case["type"]):
                    for action in ["attach", "detach"]:
                        with self.subTest(action=action):
                            func(case, action)

        return subTestWrap

    def test_link(self):
        """
            :description: Link faces or persons to list.
            :resources: '/linker'
        """
        for case in self.cases:
            with self.subTest(listType=case["type"]):
                reply = self.FacesApi.link(case["list"], action='attach', **case["params"])
                self.assertEqual(reply.statusCode, 204)
                reply = self.FacesApi.getList(case["list"])
                for obj in reply.json[case["type"]]:
                    objects = next(case["params"].values().__iter__())
                    if case["type"] == "faces":
                        self.assertIn(obj["face_id"], objects)
                    else:
                        self.assertIn(obj["person_id"], objects)

    def test_link_nonexists_accountid(self):
        """
            :description: Link faces or persons to list with nonexists accountId.
            :resources: '/linker'
        """

        @self.badCaseSubTestWrap
        def test(case, action):
            reply = self.FacesApi.link(case["list"], action=action, accountId=str(uuid4()), **case["params"])
            self.assertErrorRestAnswer(reply, 400, Error.ListNotFound)

        test(self.cases)

    def test_link_nonexists_listid(self):
        """
            :description: Link faces or persons to list with non-existing list.
            :resources: '/linker'
        """

        @self.badCaseSubTestWrap
        def test(case, action):
            reply = self.FacesApi.link(str(uuid4()), action=action, **case["params"])
            self.assertErrorRestAnswer(reply, 400, Error.ListNotFound)

        test(self.cases)

    def test_link_badformat_accountid(self):
        """
            :description: Link faces or persons to list with bad format accountId.
            :resources: '/linker'
        """

        @self.badCaseSubTestWrap
        def test(case, action):
            badAccountId = 123
            reply = self.FacesApi.link(case["list"], action=action, accountId=badAccountId, **case["params"])
            self.assertErrorRestAnswer(reply, 400, Error.BadQueryParams,
                                       msgFormat=['account_id', str(badAccountId) + ' is not of type \'string\''])

        test(self.cases)

    def test_link_badformat_listid(self):
        """
            :description: Link faces or persons to list with bad format listId.
            :resources: '/linker'
        """

        @self.badCaseSubTestWrap
        def test(case, action):
            badListId = 123
            reply = self.FacesApi.link(badListId, action=action, **case["params"])
            self.assertEqual(reply.json["error_code"], Error.BadInputJson.errorCode)

        test(self.cases)

    def test_link_nonexists_objectId(self):
        """
            :description: Link faces or persons to list with non-existing Ids. Check objects' lists.
            :resources: '/linker'
        """
        faces = copy.copy(self.faceIds)
        faces.append(str(uuid4()))
        persons = copy.copy(self.personIds)
        persons.append(str(uuid4()))

        cases = [{"params": {"personIds": persons, "listId": self.personListId}, "type": "persons",
                  "error": Error.PersonsNotFound, "getter": lambda pIds: self.FacesApi.getPersons(personIds=pIds)},
                 {"params": {"faceIds": faces, "listId": self.faceListId}, "type": "faces",
                  "error": Error.FacesNotFound, "getter": lambda fIds: self.FacesApi.getFaces(faceIds=fIds)}]

        @self.badCaseSubTestWrap
        def test(case, action):
            reply = self.FacesApi.link(action=action, **case["params"])
            self.assertErrorRestAnswer(reply, 400, case['error'])

            if action == 'attach':
                objects = (case['params'].get('faceIds') or case['params'].get('personIds'))[:-1]
                reply = case['getter'](objects)
                self.assertTrue(all(o['lists'] == [] for o in reply.json[case['type']]), reply.json)

        test(cases)

    def test_unlink(self):
        """
            :description: Unlink faces or persons from list.
            :resources: '/linker'
        """
        for case in self.cases:
            with self.subTest(listType=case["type"]):
                reply = self.FacesApi.link(case["list"], action='detach', **case["params"])
                self.assertEqual(reply.statusCode, 204)
                reply = self.FacesApi.getList(case["list"])
                for obj in reply.json[case["type"]]:
                    objects = next(case["params"].values().__iter__())
                    if case["type"] == "faces":
                        self.assertIn(obj["face_id"], objects)
                    else:
                        self.assertIn(obj["person_id"], objects)

    def test_unlink_acount_id(self):
        """
            :description: Unlink faces or persons from list with account id.
            :resources: '/linker'
        """
        for case in self.cases:
            with self.subTest(listType=case["type"]):
                reply = self.FacesApi.link(case["list"], action='detach', accountId=self.account_id, **case["params"])
                self.assertEqual(reply.statusCode, 204)
                reply = self.FacesApi.getList(case["list"])
                for obj in reply.json[case["type"]]:
                    objects = next(case["params"].values().__iter__())
                    if case["type"] == "faces":
                        self.assertIn(obj["face_id"], objects)
                    else:
                        self.assertIn(obj["person_id"], objects)

    def test_linker_allowed_methods(self):
        """
            :description: Check allowed methods for resource
            :resources: '/linker'
        """
        self.methods_test('/linker', ['patch'])
