from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import ConfigParser as configparser
from contextlib import closing

from permafreeze import set_default_options, archiver, tree, do_freeze, storage
from permafreeze import thaw

TESTFILES_PATH = os.path.abspath("../testfiles")
TESTFILES_THAW_PATH = os.path.abspath("../testfiles_thaw")

def get_test_config():
    cp = configparser.SafeConfigParser()
    cp.add_section("options")
    cp.set("options", "site-name", "test")
    cp.set("options", "s3-bucket-name", "test")
    cp.set("options", "glacier-vault-name", "test")
    cp.add_section("targets")
    cp.set("targets", "testfiles", TESTFILES_PATH)

    set_default_options(cp)
    return cp

def test_freeze():
    cp = get_test_config()

    old_tree = tree.Tree()
    st = storage.FakeStorage()
    ar = archiver.Archiver(cp, 0, 'testfiles', st)
    with closing(ar):
        new_tree = do_freeze(cp, old_tree, TESTFILES_PATH, ar, {'target-name': 'testfiles'})
        print()
        tree.print_tree(new_tree)

def test_thaw():
    cp = get_test_config()

    old_tree = tree.Tree()
    st = storage.FakeStorage()
    ar = archiver.Archiver(cp, 0, 'testfiles', st)
    with closing(ar):
        new_tree = do_freeze(cp, old_tree, TESTFILES_PATH, ar, {'target-name': 'testfiles'})

    # Thaw the new tree
    print("\nThawing")
    thaw.do_thaw(cp, new_tree, TESTFILES_THAW_PATH, st)
