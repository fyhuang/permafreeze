from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import ConfigParser as configparser
from contextlib import closing

from permafreeze import load_config, set_default_options, archiver, tree, do_freeze, storage
from permafreeze import thaw
from permafreeze.storage import AmazonStorage

TESTFILES_TGT = "testfiles"
TESTFILES_PATH = os.path.abspath("../testfiles")
TESTFILES_THAW_PATH = os.path.abspath("../testfiles_thaw")

def get_test_config():
    cp = configparser.SafeConfigParser()
    cp.add_section("options")
    cp.set("options", "site-name", "test")
    cp.set("options", "s3-bucket-name", "test")
    cp.set("options", "glacier-vault-name", "test")
    cp.set("options", "s3-create-bucket", "True")
    cp.set("options", "config-dir", "cfg")
    cp.add_section("targets")
    cp.set("targets", "testfiles", TESTFILES_PATH)

    cp.set("options", "s3-host", "127.0.0.1")
    cp.set("options", "s3-port", "4567")

    cp.add_section("auth")
    cp.set("auth", "accessKeyId", "AKID")
    cp.set("auth", "secretAccessKey", "SAK")

    set_default_options(cp)
    return cp

def test_freeze(configname):
    if configname is None:
        cp = get_test_config()
        st = storage.FakeStorage(cp)
    else:
        cp = load_config(configname)
        set_default_options(cp)
        st = storage.AmazonStorage(cp)

    old_tree = tree.Tree()
    ar = archiver.Archiver(cp, 0, TESTFILES_TGT, st)
    with closing(ar):
        new_tree = do_freeze(cp, old_tree, TESTFILES_PATH, ar, {'target-name': TESTFILES_TGT})
        print()
        tree.print_tree(new_tree)

def test_thaw():
    cp = get_test_config()

    old_tree = tree.Tree()
    st = storage.FakeStorage(cp)
    ar = archiver.Archiver(cp, 0, TESTFILES_TGT, st)
    with closing(ar):
        new_tree = do_freeze(cp, old_tree, TESTFILES_PATH, ar, {'target-name': TESTFILES_TGT})
        storage.store_local_tree(cp, TESTFILES_TGT, new_tree)

    # Thaw the new tree
    print("\nThawing")
    loaded_tree = storage.load_local_tree(cp, TESTFILES_TGT)
    thaw.do_thaw(cp, loaded_tree, TESTFILES_THAW_PATH, st)

def test_amazon_storage():
    cp = load_config('../config.ini')
    set_default_options(cp)

    st = AmazonStorage(cp)

    t = tree.Tree()
    st.save_tree(TESTFILES_TGT, t)

    os.unlink(os.path.join(cp.get('options', 'config-dir'), 'tree-testfiles'))

    si = st.get_stored_info(TESTFILES_TGT)
    print(si)


def test_storage():
    cp = get_test_config()

    t = tree.Tree()
    t.files['/test'] = tree.UukeyStorage(False, 0)
    storage.store_local_tree(cp, TESTFILES_TGT, t)
    print(os.path.isfile(storage.local_tree_fname(cp, TESTFILES_TGT)))

    nt = storage.load_local_tree(cp, TESTFILES_TGT)
    print(nt == t)
    print(t.files)
    print(nt.files)

if __name__ == "__main__":
    test_storage()
