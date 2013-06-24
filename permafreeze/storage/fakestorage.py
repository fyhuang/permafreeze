from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import shutil
import tarfile
from StringIO import StringIO

from permafreeze.storage import RemoteStoredInfo, FileCache

FAKE_STORAGE_DIR = "tmp"

class FakeStorage(object):
    def __init__(self, cp):
        self.cp = cp
        self.cache = FileCache(cp)

    def get_stored_info(self, target):
        tree_local_fname = os.path.join(self.cp.get('options', 'config-dir'), 'tree-'+target)
        return RemoteStoredInfo(tree_local_fname, tree.Tree())

    def save_tree(self, target, new_tree):
        sio = StringIO()
        tree.save_tree(new_tree, sio)

        tree_local_fname = os.path.join(self.cp.get('options', 'config-dir'), 'tree-'+target)
        with open(tree_local_fname, 'wb') as f:
            f.write(sio.getvalue())

    def save_archive(self, filename):
        if not os.path.isdir(FAKE_STORAGE_DIR):
            os.mkdir(FAKE_STORAGE_DIR)
        basename = os.path.basename(filename)
        shutil.copy(filename, os.path.join(FAKE_STORAGE_DIR, basename))
        return basename

    def load_archive(self, ar_name):
        afile = self.cache.newfile(ar_name)
        shutil.copy(os.path.join(FAKE_STORAGE_DIR, ar_name), afile.fullpath())
        return afile

