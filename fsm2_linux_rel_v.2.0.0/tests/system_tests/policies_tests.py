import unittest
from tests.system_tests.unittests_descriptor_policy import TestDescriptorPolicy
from tests.system_tests.unittests_person_policy import TestPersonPolicy
from tests.system_tests.base_test_handlers_logic import BaseTestsHandlersPolicies
from tests.system_tests.unittests_group_policy import TestGroupPolicy
from tests.system_tests.unittests_multiple_faces import TestMultipleFacesPolicy
from tests.system_tests.unittests_search_policy import TestSearchPolicy
from tests.system_tests.unittests_simple_policy import TestSimplePolicy
from tests.system_tests.unittests_extract_policies import TestExtractPolicies


def setUpModule():
    BaseTestsHandlersPolicies.setUpClass()


def tearDownModule():
    BaseTestsHandlersPolicies.tearDownClass()


class TestHandlerPoliciesPersonPolicy(TestPersonPolicy):
    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        pass


class TestHandlerPoliciesDescriptorPolicy(TestDescriptorPolicy):
    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        pass


class TestHandlerPoliciesGroupPolicy(TestGroupPolicy):
    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        TestGroupPolicy.superSetUpClass()


class TestHandlerPoliciesMultipleFacesPolicy(TestMultipleFacesPolicy):
    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        pass


class TestHandlerPoliciesSearchPolicy(TestSearchPolicy):
    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        pass


class TestHandlerPoliciesSimplePolicy(TestSimplePolicy):
    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        pass


class TestHandlerExtractPolicies(TestExtractPolicies):
    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        pass
