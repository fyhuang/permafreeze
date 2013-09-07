from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import datetime
import collections

RemoteStoredInfo = collections.namedtuple('RemoteStoredInfo',
        ['all_trees'])

TREE_DT_FMT = "%Y-%m-%dT%H:%M"


from permafreeze import tree
from permafreeze.storage.filecache import FileCache
from permafreeze.storage.localstorage import LocalStorage
from permafreeze.storage.amazonstorage import AmazonStorage


def newest_tree(cp, st, target):
    remote_tree_dt, remote_tree_key = st.newest_stored_tree(target)
    local_tree_dt = local_tree_dt(cp, target)

    if local_tree_dt >= remote_tree_dt:
        # Load local tree
        return load_local_tree(cp, target)
    else:
        tree_str = remote_tree_key.get_contents_as_string()
        return tree.tree_from_str(tree_str)
