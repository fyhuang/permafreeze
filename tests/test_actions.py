from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future import standard_library
from future.builtins import *

import os.path
import filecmp
import unittest
import shutil
import time
import stat

from tests import get_test_config, TEST_FILES_DIR, TEST_FILES_TGT
from permafreeze import tree, logger, files_to_consider
from permafreeze.freeze import do_freeze
from permafreeze.thaw import do_thaw
from permafreeze.check import do_check
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

    def testMultiFreezeLocal(self):
        # TODO: test multiple-freeze cases, e.g. shouldn't store a file
        # that's already hashed; test when file is replaced by dir of same name;
        # test when file's POSIX attrs change; test when file's mtime changes
        # but contents are identical
        conf = get_test_config()
        with conf:
            conf.st = LocalStorage(conf, conf.tempdir("testMultiFreezeLocal"))
            staging = conf.tempdir("staging", create=False)
            shutil.copytree(TEST_FILES_DIR, staging)
            conf.set("targets", TEST_FILES_TGT, staging)

            old_tree = tree.Tree()
            new_tree = do_freeze(conf, old_tree, TEST_FILES_TGT)

            # Should be a no-op
            old_tree = new_tree
            new_tree = do_freeze(conf, old_tree, TEST_FILES_TGT)
            self.assertEqual(old_tree.entries, new_tree.entries)

            # Add one file
            shutil.copy2(os.path.join(staging, "pg1661.txt"),
                    os.path.join(staging, "pg1661_copy.txt"))
            old_tree = new_tree
            new_tree = do_freeze(conf, old_tree, TEST_FILES_TGT)
            self.assertEqual(len(old_tree.entries)+1, len(new_tree.entries))

            # Change a file
            time.sleep(0.2)
            with open(os.path.join(staging, "12407-0.txt"), 'w') as f:
                f.write('blah blah')
            old_tree = new_tree
            new_tree = do_freeze(conf, old_tree, TEST_FILES_TGT)
            self.assertNotEqual(old_tree.entries['/12407-0.txt'].last_hashed,
                    new_tree.entries['/12407-0.txt'].last_hashed)

            # Change some POSIX attrs
            time.sleep(0.2)
            os.chmod(os.path.join(staging, "pg1661.txt"), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            old_tree = new_tree
            new_tree = do_freeze(conf, old_tree, TEST_FILES_TGT)
            new_entry = new_tree.entries['/pg1661.txt']
            self.assertNotEqual(old_tree.entries['/pg1661.txt'].last_hashed,
                    new_entry.last_hashed)
            self.assertEqual(new_entry.posix_perms & stat.S_IXUSR, stat.S_IXUSR)
            self.assertNotEqual(new_entry.posix_perms & stat.S_IRGRP, stat.S_IRGRP)
            self.assertNotEqual(new_entry.posix_perms & stat.S_IROTH, stat.S_IROTH)


    def testThawLocal(self):
        conf = get_test_config()
        with conf:
            conf.st = LocalStorage(conf, conf.tempdir("testThawLocal"))
            old_tree = tree.Tree()
            new_tree = do_freeze(conf, old_tree, TEST_FILES_TGT)
            tree.print_tree(new_tree)

            # Now thaw
            thawdir = conf.tempdir("thaw_dir")
            do_thaw(conf, new_tree, thawdir)

            # Directory diff
            for (full_path, target_path) in files_to_consider(conf, TEST_FILES_TGT):
                fthaw = os.path.join(thawdir, target_path[1:])
                self.assertTrue(filecmp.cmp(full_path, fthaw))

    def testCheckLocal(self):
        conf = get_test_config()
        with conf:
            conf.st = LocalStorage(conf, conf.tempdir("testCheckLocal"))
            old_tree = tree.Tree()
            new_tree = do_freeze(conf, old_tree, TEST_FILES_TGT)
            
            # Now check
            logger.reset_cb()
            do_check(conf, new_tree, TEST_FILES_TGT)
