from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future import standard_library
from future.builtins import *

import os.path
import unittest
from tests import get_test_config

class TestPfConfig(unittest.TestCase):
    def testConfigCleanup(self):
        self.conf = get_test_config()
        with self.conf:
            tdir = self.conf.tempdir('test1')
            fname = os.path.join(tdir, 'file1.txt')
            with open(fname, 'w') as f:
                f.write('Test data')

        # Test that everything is gone
        self.assertFalse(os.path.exists(fname))
        self.assertFalse(os.path.exists(os.path.dirname(fname)))
        self.assertFalse(os.path.exists(tdir))
