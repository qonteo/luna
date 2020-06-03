from tests.unittests_person import TestPerson
from tests.unittests_registration import TestRegistration
from tests.unittests_version import TestVersion
from tests.unittests_account import TestAccount
from tests.unittests_create_person import TestCreatePerson
from tests.unittests_extract_image import TestImage
from tests.unittests_extract_with_query_params import TestImageWithQueries
from tests.unittests_linkDescriptor import TestLinkDescriptor
from tests.unittests_linkList import TestLinkList
from tests.unittests_list import TestList
from tests.unittests_linkPhotoToList import TestPhotoLinkList
from tests.unittests_descriptor import TestDescriptor
from tests.unittests_linkAsync import TestAsyncLink
from tests.unittests_get_persons import TestGetPersons
from tests.unittests_headers import TestHeaders
from tests.matcher.unittests_matching_complex import TestMatchingComplex
from tests.matcher.unittests_matching_identify import TestMatchingIdentify
from tests.matcher.unittests_matching_match import TestMatchingMatch
from tests.matcher.unittests_matching_search import TestMatchingSearch
from tests.matcher.unittests_matching_verify import TestMatchingVerify
from tests.unittests_linker import TestLinker
import unittest


if __name__ == '__main__':
    suite = unittest.TestSuite()
    runner = unittest.TextTestRunner(suite)

