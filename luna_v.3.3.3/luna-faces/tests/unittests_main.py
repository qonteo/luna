from tests.unittests_version import TestGetVersion
from tests.unittests_list import TestList
from tests.unittests_face import TestFace
from tests.unittests_lists import TestLists
from tests.unittests_faces import TestFaces
from tests.unittests_lists_descriptors import TestListsDescriptors
from tests.unittests_linker import TestLinker
from tests.unittests_facelinker import TestFaceLinker
from tests.unittests_person import TestPerson
from tests.unittests_persons import TestPersons
from tests.unittests_request_id import TestRequestId
from tests.unittests_request_time import TestRequestTime
from tests.unittests_gc import TestGc
from tests.unittests_faces_attributes import TestFacesAttributes
from tests.unittests_persons_attributes import TestPersons
from tests.unittests_attributes import TestAttributes

import unittest

if __name__ == '__main__':
    suite = unittest.TestSuite()
    runner = unittest.TextTestRunner(suite)
