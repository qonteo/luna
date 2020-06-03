import os
import sys
import unittest.main

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.system_tests.unittests_handlers import TestHandlersAPI
from tests.system_tests.unittests_groups_filters import TestGroups
from tests.system_tests.unittests_groups_stat import TestStatGroups
from tests.system_tests.unittests_events_filters import TestEvents
from tests.system_tests.unittests_events_stat import TestStatEvents
from tests.system_tests.unittests_websockets import TestWebSockets
from tests.system_tests.unittests_top_n import TestsHitTopN
from tests.system_tests.unittests_linker import LinkingTest
from tests.system_tests.unittests_cross_mach import CrossMatchTest, CrossMatchSimTest
from tests.system_tests.unittests_clusterization import TestsClusterization
from tests.system_tests.unittests_reporter import ReporterTest
from tests.system_tests.policies_tests import TestHandlerPoliciesPersonPolicy, TestHandlerPoliciesDescriptorPolicy, \
    TestHandlerPoliciesGroupPolicy, TestHandlerPoliciesSearchPolicy, TestHandlerPoliciesMultipleFacesPolicy, \
    TestHandlerPoliciesSimplePolicy, TestHandlerExtractPolicies
from tests.system_tests.unittests_version import TestVersion

os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestHandlersAPI())
    runner = unittest.TextTestRunner(suite)
