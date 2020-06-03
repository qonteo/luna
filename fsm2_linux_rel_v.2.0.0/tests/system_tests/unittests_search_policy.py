from tests.system_tests.handlers.search_policy_handler import SearchPolicyHandler


class TestSearchPolicy(SearchPolicyHandler):

    def test_handlers_search_by_persons_and_descriptors_lists_and__by_3_list(self):
        handlers = [self.create_handlers_search_persons(), self.create_handler_search_by_3_list()]
        for handler in handlers:
            with self.subTest(handler=handler):
                reply = self.create_event(1, handler)
                event_search = reply[0][0].json['events'][0]['search']
                handler = reply[0][1]
                data = reply[0][2]
                self.validateEvent(reply[0][0], handler)
                self.assertEqual(len(event_search), 3, handler['name'])
                self.assertTrue(event_search[0]['list_id'] == data["list_id"])
                self.assertTrue(event_search[0]['candidates'][0]['similarity'] == 1)

    def test_handlers_search_priority_2(self):
        """
        .. test:: test_handlers_search_priority_2
            :resources: "/handlers"
            :description: false handlers search priority 2 list
        """
        for warped_flag in self.warped_flags:
            with self.subTest(warped_flag=warped_flag):
                reply = self.create_event(warped_flag, self.create_handlers_search_priority_2())
                event_search = reply[0][0].json['events'][0]['search']
                handler = reply[0][1]
                self.validateEvent(reply[0][0], handler)
                if warped_flag == 0:
                    self.assertEqual(len(event_search), 3, handler["name"])
                else:
                    self.assertEqual(len(event_search), 1, handler["name"])
