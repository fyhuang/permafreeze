from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import unittest

from tests import get_test_config, TEST_FILES_DIR, TEST_FILES_TGT
from permafreeze.storage import FileCache

class TestFileCache(unittest.TestCase):
    def setUp(self):
        self.conf = get_test_config()
        self.fc = FileCache(self.conf)

    def tearDown(self):
        self.conf.cleanup()

    def testFileCache(self):
        cf1 = self.fc.newfile('ar123.tar')
        self.assertEqual(cf1.filename, 'ar123.tar')
        with open(cf1.fullpath(), 'wb') as f:
            f.write("Hello test world")
        self.assertEqual(self.fc.compute_size(), len("Hello test world"))

    def testCleanup(self):
        def makefile():
            cf1 = self.fc.newfile('ar123.tar')
            with open(cf1.fullpath(), 'wb') as f:
                f.write("Hello test world")
            return cf1.fullpath()

        fullpath = makefile()

        # Now the file should be unused
        self.assertTrue('ar123.tar' in self.fc.can_delete)
        self.fc.cleanup()
        self.assertFalse(os.path.exists(fullpath))

