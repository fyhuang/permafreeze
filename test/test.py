from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import ConfigParser as configparser
from contextlib import closing

from permafreeze import set_default_options, archiver, tree, do_freeze, storage
from permafreeze import thaw
from permafreeze.storage import AmazonStorage

TESTFILES_PATH = os.path.abspath("../testfiles")
TESTFILES_THAW_PATH = os.path.abspath("../testfiles_thaw")

def get_test_config():
    cp = configparser.SafeConfigParser()
    cp.add_section("options")
    cp.set("options", "site-name", "test")
    cp.set("options", "s3-bucket-name", "test")
    cp.set("options", "glacier-vault-name", "test")
    cp.set("options", "s3-create-bucket", "True")
    cp.add_section("targets")
    cp.set("targets", "testfiles", TESTFILES_PATH)

    cp.set("options", "s3-host", "127.0.0.1")
    cp.set("options", "s3-port", "4567")

    cp.add_section("auth")
    cp.set("auth", "accessKeyId", "AKID")
    cp.set("auth", "secretAccessKey", "SAK")

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

def test_amazon_storage():
    cp = get_test_config()
    st = AmazonStorage()
    st.connect(cp)
    st.s3_conn.create_bucket("test")

    t = tree.Tree()
    st.save_tree(cp, 'testfiles', t)

    si = st.get_stored_info(cp, 'testfiles')
    print(si)
