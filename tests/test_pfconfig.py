from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import unittest
from tests import get_test_config

class TestPfConfig(unittest.TestCase):
    def testConfigCleanup(self):
        self.conf = get_test_config()
        with self.conf:
            fname = os.path.join(self.conf.tempdir('test1'), 'file1.txt')
            with open(fname, 'w') as f:
                f.write('Test data')

        # Test that everything is gone
        self.assertFalse(os.path.exists(fname))
        self.assertFalse(os.path.exists(os.path.dirname(fname)))
