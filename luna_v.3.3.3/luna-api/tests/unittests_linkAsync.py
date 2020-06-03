import tornado

from tests.classes import TestBase, authStr, authArr
from tornado.ioloop import IOLoop
from tornado import gen
from tests.functions import createPayloadImg
from tests.resources import warpedImage
from tests import luna_api_functions


@gen.coroutine
def asyncCreateDescriptors(headers):
    descriptorFutures = []
    binBody = createPayloadImg(warpedImage)
    for i in range(10):
        future = luna_api_functions.extractDescriptors(authData=headers, body=binBody, warpedImage=True,
                                                       asyncRequest=True)
        descriptorFutures.append(future)
    descriptorIds = []
    for future in descriptorFutures:
        reply = yield future
        descriptorIds.append(reply.body["faces"][0]["id"])
    return descriptorIds


class TestAsyncLink(TestBase):
    """
    Simultaneously attach object to list
    """

    def setUp(self):
        self.createAccountAndToken()

    def authorization(self, func):
        @gen.coroutine
        def wrap(*func_args, **func_kwargs):
            for auth in authArr:
                with self.subTest(auth=auth):
                    if auth == "basic":
                        headers = luna_api_functions.createAuthHeader('login')
                    else:
                        headers = luna_api_functions.createAuthHeader('token', self.token)
                    yield func(headers, self.token, *func_args, **func_kwargs)
            return

        return wrap

    def runAsyncTest(self, func):

        @self.authorization
        def test(headers, auth):
            def runTest():
                try:
                    IOLoop.current().run_sync(lambda: func(auth, headers))
                    self.failure = False
                except Exception as e:
                    self.failure = e
                    raise e

            self.failure = None
            runTest()
            if self.failure:
                raise self.failure

        test()

    def test_async_link_link_descriptors_to_list(self):
        """
        .. test:: test_async_link_link_descriptors_to_list

            :resources: "/storage/descriptors/\{descriptor_id\}/linked_lists"
            :description: success simultaneously attaching descriptors to list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        @gen.coroutine
        def testLinkDescriptorsToList(auth, headers):

            descriptorIds = yield asyncCreateDescriptors(auth)

            listResponse = yield luna_api_functions.createList(auth, False, asyncRequest=True)
            listId = listResponse.body["list_id"]
            futures = []
            for descriptorId in descriptorIds:
                future = luna_api_functions.linkListToDescriptor(auth, descriptorId, listId, 'attach',
                                                                 asyncRequest=True)
                futures.append(future)

            for future in futures:
                reply = yield future
                self.assertEqual(reply.statusCode, 204, authStr(headers))

        tornado.ioloop.IOLoop.instance().run_sync(testLinkDescriptorsToList)

    def test_async_link_link_persons_to_list(self):
        """
        .. test:: test_async_link_link_persons_to_list

            :resources: "/storage/persons/\{person_id\}/linked_lists"
            :description: success simultaneously attaching persons to list
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        @gen.coroutine
        def testLinkPersonsToList(auth, headers):

            personIds = []

            descriptorIds = yield asyncCreateDescriptors(auth)

            for descriptorId in descriptorIds:
                personResponse = yield luna_api_functions.createPerson(auth, asyncRequest=True)
                personId = personResponse.body["person_id"]
                luna_api_functions.linkDescriptorToPerson(auth, personId, descriptorId, "attach", asyncRequest=True)
                # self.linkPersonToPhoto(headers, descriptorId, personId)
                personIds.append(personId)

            listResponse = yield luna_api_functions.createList(auth, False, asyncRequest=True)
            listId = listResponse.body["list_id"]

            futures = []
            for personId in personIds:
                future = luna_api_functions.linkListToPerson(auth, personId, listId, 'attach', asyncRequest=True)
                futures.append(future)

            for future in futures:
                reply = yield future
                self.assertEqual(reply.statusCode, 204, authStr(headers))

        tornado.ioloop.IOLoop.instance().run_sync(testLinkPersonsToList)

    def test_async_link_link_descriptors_to_person(self):
        """
        .. test:: test_async_link_link_descriptors_to_person

            :resources: "/storage/persons/\{person_id\}/linked_descriptors"
            :description: success simultaneously attaching descriptors to person
            :LIS: No
            :tag: Linking
        """

        @self.authorization
        @gen.coroutine
        def testLinkDescriptorsToPerson(auth, headers):

            descriptorIds = yield asyncCreateDescriptors(auth)

            listResponse = yield luna_api_functions.createList(auth, False, asyncRequest=True)
            listId = listResponse.body["list_id"]

            personResponse = yield luna_api_functions.createPerson(auth, asyncRequest=True)
            personId = personResponse.body["person_id"]
            descriptorResponse = yield luna_api_functions.extractDescriptors(auth, filename=warpedImage,
                                                                             warpedImage=True, asyncRequest=True)
            descriptorId = descriptorResponse.body["faces"][0]["id"]
            yield luna_api_functions.linkDescriptorToPerson(auth, personId, descriptorId, "attach", asyncRequest=True)

            future = luna_api_functions.linkListToPerson(auth, personId, listId, 'attach', asyncRequest=True)
            reply = yield future

            self.assertEqual(reply.statusCode, 204, authStr(headers))

            futures = []

            for descriptorId in descriptorIds:
                future = luna_api_functions.linkDescriptorToPerson(auth, personId, descriptorId, 'attach',
                                                                   asyncRequest=True)
                futures.append(future)

            for future in futures:
                reply = yield future
                self.assertEqual(reply.statusCode, 204, authStr(headers))

        tornado.ioloop.IOLoop.instance().run_sync(testLinkDescriptorsToPerson)
