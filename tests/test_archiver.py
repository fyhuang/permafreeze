from __future__ import division, absolute_import, print_function, unicode_literals

import unittest

from tests import get_test_config

class TestArchiver(unittest.TestCase):
    def setUp(self):
        self.conf = get_test_config()
        self.ar = Archiver(self.conf, 'testtarget')

    def tearDown(self):
        self.conf.cleanup()

    def testArchiver(self):
        archives = []
        def test_cb(uuid, archive_path):
            archives.append((uuid, archive_path))

        self.ar.set_callback(test_cb)

