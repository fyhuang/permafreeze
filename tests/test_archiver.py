from __future__ import division, absolute_import, print_function, unicode_literals

import glob
import unittest

from tests import get_test_config, TEST_FILES_DIR, TEST_FILES_TGT
from permafreeze import uukey_and_size
from permafreeze.archiver import Archiver

class TestArchiver(unittest.TestCase):
    def setUp(self):
        self.conf = get_test_config()
        self.ar = Archiver(self.conf, TEST_FILES_TGT)

    def tearDown(self):
        self.conf.cleanup()

    def testArchiver(self):
        archives = []
        def test_cb(uuid, archive_path):
            archives.append((uuid, archive_path))

        self.ar.set_callback(test_cb)
        for f in glob.glob('{}/*'.format(TEST_FILES_DIR)):
            uukey, size = uukey_and_size(f)
            self.ar.add_file(f, uukey, size)
        self.ar.close()

        print(archives)

