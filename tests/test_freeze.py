from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import unittest

from tests import get_test_config, TEST_FILES_DIR, TEST_FILES_TGT
from permafreeze import tree, do_freeze
from permafreeze.storage import LocalStorage

class TestFreeze(unittest.TestCase):
    def testFreezeLocal(self):
        conf = get_test_config()
        with conf:
            conf.st = LocalStorage(conf, conf.tempdir("testFreezeLocal"))
            old_tree = tree.Tree()
            new_tree = do_freeze(conf, old_tree, TEST_FILES_TGT)
            tree.print_tree(new_tree)
