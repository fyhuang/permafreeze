from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future import standard_library
from future.builtins import *

import os
import os.path
import time
import stat
import unittest
from datetime import datetime

from tests import get_test_config

class TestDateTime(unittest.TestCase):
    def testOSXMtime(self):
        conf = get_test_config()
        with conf:
            tempdir = conf.tempdir("testOSXMtime")
            fname = os.path.join(tempdir, "test.txt")

            now_dt = datetime.utcnow()
            with open(fname, "w") as f:
                f.write("test")

            sb = os.stat(fname)
            mt = os.path.getmtime(fname)
            self.assertEqual(sb.st_mtime, mt)

            mt_dt = datetime.utcfromtimestamp(mt)
            time_diff = abs(mt_dt - now_dt)
            self.assertTrue(time_diff.seconds < 5)
