from tests.system_tests.handlers.person_policy_handler import PersonPolicyHandler
from tests.system_tests.base_test_handlers_logic import *


class TestPersonPolicy(PersonPolicyHandler):

    def test_handlers_person_create_simple_policy(self):
        """
        .. test:: test_handlers_person_create_simple_policy
            :resources: "/handlers"
            :description: test handlers person create simple policy warp -1 ,0, 1
        """
        handlers_data = self.create_handlers_person_policy_or_person_policy_user_data(policyname="simple_person_policy")
        for imgAndList in handlers_data:
            for warped_flag in self.warped_flags:
                with self.subTest(warped_flag=warped_flag):
                    reply = emitEvent(imgAndList[1]['id'],
                                      imgAndList[0][0]['img'],
                                      queryParams={"warped_image": warped_flag})
                    self.validateEvent(reply, imgAndList[1], checkPerson=True)

    def test_handlers_person_create_user_data(self):
        """
        .. test:: test_handlers_person_create_user_data
            :resources: "/handlers"
            :description: test handlers person create user data
        """
        handlers_data = self.create_handlers_person_policy_or_person_policy_user_data("person_policy_user_data")
        for imgAndList in handlers_data:
            reply = emitEvent(imgAndList[1]["id"],
                              imgAndList[0][0]['img'],
                              queryParams={"warped_image": 1, "user_data": "test_visionlabs_user_data"})
            self.validateEvent(reply, imgAndList[1], checkPerson=True)
            personId = reply.json["events"][0]["person_id"]
            person = TestPersonPolicy.lunaClient.getPerson(personId)
            self.assertEqual("test_visionlabs_user_data", person.body["user_data"])

    def test_handlers_person_create_with_filters(self):
        """
        .. test:: test_handlers_person_create_with_filters
            :resources: "/handlers"
            :description: test handlers person create with filters
        """
        handlers_data = self.create_handlers_person_with_filters()
        for handler_data in handlers_data:
            for countImg, img in enumerate(handler_data[0]):
                for handlers in handlers_data:
                    for counthandler, handler in enumerate(handlers[1]):
                        reply = emitEvent(handler['id'], img, queryParams={"warped_image": 1})
                        if countImg != counthandler:
                            self.assertTrue(reply.json["events"][0]["person_id"] is None)
                        else:
                            self.validateEvent(reply, handler, checkPerson=True)

    def test_handlers_person_create_with_several_filters(self):
        """
        .. test_handlers_person_create_with_several_filters
            :resources: "/handlers"
            :description: test handlers person create with several filters
        """
        handlers_data = self.create_handlers_person_create_with_several_filters()
        for imgAndList in handlers_data:
            handler = imgAndList[1]
            for countImg, img in enumerate(imgAndList[0]):
                reply = emitEvent(handler['id'], img, queryParams={"warped_image": 1})
                if countImg == 0:
                    self.assertTrue(reply.json["events"][0]["person_id"] is None)
                else:
                    self.validateEvent(reply, handler, checkPerson=True)

    def test_handlers_person_create_with_similarity_policy_2(self):
        """
        .. test_handlers_person_create_with_similarity_policy_2
            :resources: "/handlers"
            :description: test handlers person create with similarity policy 2
        """
        handlers_data = self.create_handlers_person_with_similarity_policy_2()
        for imgAndList in handlers_data:
            handler = imgAndList[1]
            for countImg, img in enumerate(imgAndList[0]):
                reply = emitEvent(handler['id'], img, queryParams={"warped_image": 1})
                if countImg == 0:
                    self.assertTrue(reply.json["events"][0]["person_id"] is None)
                else:
                    self.validateEvent(reply, handler, checkPerson=True)

    def test_handlers_person_attach_simple(self):
        """
        .. test_handlers_person_attach_simple
            :resources: "/handlers"
            :description: test handlers person attach simple
        """
        handlers_data = self.create_handlers_person_attach_simple()
        for handlers in handlers_data:
            reply = emitEvent(handlers[0][1]['id'], handlers[0][0]['img'], queryParams={"warped_image": 1})
            self.validateEvent(reply, handlers[0][1], checkPerson=True,
                               personsLists=[TestPersonPolicy.personsAttachLists[0]])

    def test_handlers_person_attach_policy_with_one_filter(self):
        """
        .. test_handlers_person_attach_policy_with_one_filter
            :resources: "/handlers"
            :description: test handlers person attach policy with one filter
        """
        handlers_data = self.create_handlers_person_attach_policy_with_one_filter()
        for handler in handlers_data:
            for imgData in handler[0]:
                reply = emitEvent(handler[1]['id'], imgData["img"], queryParams={"warped_image": 1})
                self.validateEvent(reply, handler[1], personsLists=imgData["attaching_list"])

    def test_handlers_person_attach_with_several_filters(self):
        """
        .. test_handlers_person_attach_with_several_filters
            :resources: "/handlers"
            :description: test handlers person attach with several filters
        """
        handlers_data = self.create_handlers_person_attach_policy_with_several_filters()
        for handler in handlers_data:
            for imgData in handler[0]:
                reply = emitEvent(handler[1]['id'], imgData["img"], queryParams={"warped_image": 1})
                self.validateEvent(reply, handler[1], personsLists=imgData["attaching_list"])

    def test_handlers_person_attach_policy_with_one_filter2(self):
        """
        .. test_handlers_person_attach_policy_with_one_filter2
            :resources: "/handlers"
            :description: test handlers person attach policy with one filter2
        """
        handlers_data = self.create_handlers_person_attach_policy_with_one_filter2()
        for handler in handlers_data:
            for imgData in handler[0]:
                reply = emitEvent(handler[1]['id'], imgData["img"], queryParams={"warped_image": 1})
                self.validateEvent(reply, handler[1], personsLists=imgData["attaching_list"])
