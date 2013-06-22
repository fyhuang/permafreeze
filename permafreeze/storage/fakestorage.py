from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import shutil
import tarfile

from permafreeze.storage import RemoteStoredInfo

FAKE_STORAGE_DIR = "tmp"

class FakeStorage(object):
    def get_stored_info(self, cp, target):
        tree_local_fname = os.path.join(cp.get('options', 'config-dir'), 'tree-'+target)
        return RemoteStoredInfo(tree_local_fname, tree.Tree())

    def save_tree(self, cp, target, new_tree):
        pass

    def save_archive(self, cp, filename):
        if not os.path.isdir(FAKE_STORAGE_DIR):
            os.mkdir(FAKE_STORAGE_DIR)
        basename = os.path.basename(filename)
        shutil.copy(filename, os.path.join(FAKE_STORAGE_DIR, basename))
        return basename

    def load_archive(self, cp, ar_name):
        return os.path.join(FAKE_STORAGE_DIR, ar_name)

