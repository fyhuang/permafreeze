from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import shutil

from permafreeze import mkdir_p
from permafreeze.storage import RemoteStoredInfo, FileCache

class LocalStorageKey(object):
    pass

class LocalStorage(object):
    def __init__(self, cp, target_dir):
        self.cp = cp
        self.cache = FileCache(cp)

        self.target_dir = target_dir
        self.trees_dir = os.path.join(target_dir, 'trees')
        self.archives_dir = os.path.join(target_dir, 'archives')

        mkdir_p(self.trees_dir)
        mkdir_p(self.archives_dir)

    def get_stored_info(self, target):
        return RemoteStoredInfo(tree_local_fname, [])

    def save_tree(self, target, new_tree):
        now_dt = datetime.utcnow()
        tree_local_fname = os.path.join(self.trees_dir, now_dt.strftime('%Y%m%dT%H%M'))
        with open(tree_local_fname, 'wb') as f:
            tree.save_tree(new_tree, f)

    def save_archive(self, filename):
        archive_id = hashlib.sha224(filename).hexdigest()
        shutil.copy(filename, os.path.join(self.archives_dir, archive_id))
        return archive_id

    def load_archive(self, ar_name):
        afile = self.cache.newfile(ar_name)
        shutil.copy(os.path.join(FAKE_STORAGE_DIR, ar_name), afile.fullpath())
        return afile

