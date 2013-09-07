from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import json
import shutil
from datetime import datetime

from permafreeze import mkdir_p, tree
from permafreeze.storage import RemoteStoredInfo, FileCache
from permafreeze.storage import TREE_DT_FMT

class LocalStorageKey(object):
    def __init__(self, filename):
        self.filename = filename
        with open('{}.meta'.format(self.filename), 'rb') as f:
            self.meta = json.load(f)

    def get_metadata(self, key):
        return self.meta[key]

    def get_contents_as_string(self):
        with open(self.filename, 'rb') as f:
            return f.read()

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
        tree_fns = (os.path.join(self.trees_dir, fn) for fn in os.listdir(self.trees_dir))
        return RemoteStoredInfo([LocalStorageKey(fn) for fn in tree_fns
                    if os.path.isfile(fn) and not fn.endswith('.meta')])

    def save_tree(self, target, new_tree):
        now_dt = datetime.utcnow()
        now_dt_str = now_dt.strftime(TREE_DT_FMT)
        tree_local_fname = os.path.join(self.trees_dir,
                '{}-{}'.format(target, now_dt_str))
        with open(tree_local_fname, 'wb') as f:
            tree.save_tree(new_tree, f)
        with open('{}.meta'.format(tree_local_fname), 'wb') as f:
            json.dump({'pf:target': target, 'pf:saved_dt': now_dt_str}, f)

    def save_archive(self, filename):
        archive_id = hashlib.sha224(filename).hexdigest()
        shutil.copy(filename, os.path.join(self.archives_dir, archive_id))
        return archive_id

    def load_archive(self, ar_name):
        afile = self.cache.newfile(ar_name)
        shutil.copy(os.path.join(FAKE_STORAGE_DIR, ar_name), afile.fullpath())
        return afile

