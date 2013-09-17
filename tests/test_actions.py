from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import unittest

from tests import get_test_config, TEST_FILES_DIR, TEST_FILES_TGT
from permafreeze import tree, logger
from permafreeze.freeze import do_freeze
from permafreeze.thaw import do_thaw
from permafreeze.storage import LocalStorage

class TestActions(unittest.TestCase):
    def setUp(self):
        logger.set_cb(None)

    def testFreezeLocal(self):
        conf = get_test_config()
        with conf:
            conf.st = LocalStorage(conf, conf.tempdir("testFreezeLocal"))
            old_tree = tree.Tree()
            new_tree = do_freeze(conf, old_tree, TEST_FILES_TGT)
            tree.print_tree(new_tree)

    def testThawLocal(self):
        conf = get_test_config()
        with conf:
            conf.st = LocalStorage(conf, conf.tempdir("testThawLocal"))
            old_tree = tree.Tree()
            new_tree = do_freeze(conf, old_tree, TEST_FILES_TGT)
            tree.print_tree(new_tree)

            # Now thaw
            destdir = conf.tempdir("thaw_dir")
            do_thaw(conf, new_tree, destdir)

    def testCheckLocal(self):
        pass
