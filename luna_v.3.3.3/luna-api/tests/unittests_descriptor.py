from tests.classes import TestBase, authStr
from tests import luna_api_functions
from datetime import datetime
import time



class TestDescriptor(TestBase):
    """
    Test get descriptor
    """
    def setUp(self):
        self.createAccountAndToken()
        headers = luna_api_functions.createAuthHeader()
        self.photoId = TestBase.createPhoto(headers)

    def test_descriptor_get_descriptorData(self):
        """
        .. test:: test_descriptor_get_descriptorData

            :resources: "/storage/descriptors/\{descriptor_id\}"
            :description: success getting descriptor
            :LIS: No
            :tag: Descriptor
        """

        @self.authorization
        def getDescriptorDataTest(headers, auth):
            replyInfo = luna_api_functions.getDescriptor(headers, self.photoId)
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            self.assertEqual(replyInfo.body["id"], self.photoId, authStr(auth))
            self.assertTrue("last_update" in replyInfo.body, authStr(auth))
            self.assertTrue(replyInfo.body["person_id"] is None, authStr(auth))

        getDescriptorDataTest()

    def test_descriptor_last_update(self):
        """
        .. test:: test_descriptor_last_update

            :resources: "/storage/descriptors"
            :description: success getting descriptor with last_update
            :LIS: No
            :tag: Descriptor
        """

        @self.authorization
        def checkLastUpdate(headers, auth):
            photoId = TestBase.createPhoto(headers)

            replyInfo = luna_api_functions.getDescriptor(headers, photoId)
            self.assertIn("last_update", replyInfo.body, authStr(auth))
            self.assertEqual(replyInfo.statusCode, 200, authStr(auth))
            last_update = datetime.strptime(replyInfo.body["last_update"],
                                            '%Y-%m-%dT%H:%M:%S.%fZ' if '.' in replyInfo.body[
                                                "last_update"] else '%Y-%m-%dT%H:%M:%SZ')
            last_update = datetime.timestamp(last_update)
            current_time = time.time() + time.timezone
            difference_time = current_time - last_update
            self.assertTrue(difference_time <= 2, authStr(auth))

        checkLastUpdate()

    def test_descriptor_person_id(self):
        """
        .. test:: test_descriptor_person_id

            :resources: "/storage/descriptors"
            :description: success getting descriptor with person_id
            :LIS: No
            :tag: Descriptor
        """

        @self.authorization
        def check_person_id(headers, auth):
            photoId = TestBase.createPhoto(headers)
            personId = luna_api_functions.createPerson(headers).body['person_id']
            luna_api_functions.linkDescriptorToPerson(headers, personId, photoId, "attach")
            self.assertTrue("person_id" in luna_api_functions.getDescriptor(headers, photoId).body, authStr(auth))
            self.assertEqual(personId, luna_api_functions.getDescriptor(headers, photoId).body['person_id'],
                             authStr(auth))

        check_person_id()
