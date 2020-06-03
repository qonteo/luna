import unittest

from account_test import TestAccount
from account_tokens_test import TestAccountTokens
from accounts_test import TestAccounts
from list_test import TestList
from lists_test import TestLists
from person_test import TestPerson
from persons_test import TestPersons
from search_test import TestSearch
from statistic_test import TestStatistic
from grafana_test import TestGrafana
from config_test import TestConfig
from reextract_descriptors import TestReExtract
from gc_old_descriptors_test import TestGcOldDescriptorsOfAccount
from unitests_headers import TestHeaders

if __name__ == '__main__':
    suite = unittest.TestSuite()
    runner = unittest.TextTestRunner(suite)
