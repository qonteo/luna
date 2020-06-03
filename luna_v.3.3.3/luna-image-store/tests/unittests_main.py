from unittests_image import TestImage
from unittests_images import TestImages
from unittests_bucket import TestBucket
from unittests_buckets import TestBuckets
from unittests_headers import TestHeaders
from unittests_version import TestVersion
from unittests_object import TestObject
from unittests_objects import TestObjects
import unittest


if __name__ == '__main__':
    suite = unittest.TestSuite()
    runner = unittest.TextTestRunner(suite)
