from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import datetime
import collections

RemoteStoredInfo = collections.namedtuple('RemoteStoredInfo',
        ['tree_local_fname', 'all_trees'])

from permafreeze import tree
from permafreeze.storage.filecache import FileCache
from permafreeze.storage.fakestorage import LocalStorage
from permafreeze.storage.amazonstorage import AmazonStorage


def local_tree_fname(cp, target):
    return os.path.join(cp.get('options', 'config-dir'),
            'tree-{}'.format(target))

def store_local_tree(cp, target, tree_to_save, timestamp=None):
    tree_fname = local_tree_fname(cp, target)
    if timestamp is None:
        timestamp = datetime.datetime.now()
    with open(tree_fname, 'w') as f:
        tree_to_save.generated_dt = timestamp
        tree.save_tree(tree_to_save, f)

def load_local_tree(cp, target):
    tree_fname = local_tree_fname(cp, target)
    with open(tree_fname, 'r') as f:
        return tree.tree_from_str(f.read())

def local_tree_dt(cp, target):
    tree_fname = local_tree_fname(cp, target)
    with open(tree_fname, 'r') as f:
        return tree.generated_dt_from_str(f.read())

def newest_tree(cp, st, target):
    remote_tree_dt, remote_tree_key = st.newest_stored_tree(target)
    local_tree_dt = local_tree_dt(cp, target)

    if local_tree_dt >= remote_tree_dt:
        # Load local tree
        return load_local_tree(cp, target)
    else:
        tree_str = remote_tree_key.get_contents_as_string()
        return tree.tree_from_str(tree_str)
