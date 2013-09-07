from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import unittest
from StringIO import StringIO

from tests import get_test_config, TEST_FILES_TGT
from permafreeze import tree
from permafreeze.storage import LocalStorage, TREE_DT_FMT

class TestLocalStorage(unittest.TestCase):
    def setUp(self):
        self.conf = get_test_config()
        self.ls = LocalStorage(self.conf, self.conf.tempdir("localstorage"))

    def tearDown(self):
        self.conf.cleanup()

    def testLocalStorage(self):
        rsi = self.ls.get_stored_info(TEST_FILES_TGT)
        self.assertEqual(len(rsi.all_trees), 0)

        self.ls.save_tree(TEST_FILES_TGT, tree.Tree())
        rsi = self.ls.get_stored_info(TEST_FILES_TGT)
        self.assertEqual(len(rsi.all_trees), 1)

        # TODO: load the tree again

    def testLocalStorageKey(self):
        newt = tree.Tree()
        self.ls.save_tree(TEST_FILES_TGT, newt)
        trees = self.ls.get_stored_info(TEST_FILES_TGT).all_trees
        for t in trees:
            self.assertEqual(t.get_metadata('pf:target'), TEST_FILES_TGT)
            self.assertEqual(len(t.get_metadata('pf:saved_dt')), len(TREE_DT_FMT)+2)
            with self.assertRaises(KeyError):
                t.get_metadata('doesnt_exist')

            sio = StringIO()
            tree.save_tree(newt, sio)
            self.assertEqual(len(t.get_contents_as_string()), len(sio.getvalue()))

