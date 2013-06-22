from __future__ import division, absolute_import, print_function, unicode_literals

import collections

RemoteStoredInfo = collections.namedtuple('RemoteStoredInfo',
        ['tree_local_fname', 'last_tree'])

from permafreeze.storage.fakestorage import FakeStorage
from permafreeze.storage.amazonstorage import AmazonStorage
