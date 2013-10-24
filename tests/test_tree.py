from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future import standard_library
from future.builtins import *

import unittest

from permafreeze import tree

class TestTree(unittest.TestCase):
    def testTreeCopy(self):
        t = tree.Tree()
        self.assertEquals(t.entries, {})
        t.entries['/testfile'] = tree.SymlinkEntry('/nonexist')

        nt = t.copy()
        self.assertEquals(t.entries, nt.entries)
