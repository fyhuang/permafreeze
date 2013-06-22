from __future__ import division, absolute_import, print_function, unicode_literals

import struct
import pickle
import collections
import StringIO as stringio

TREE_VER_P1 = 0

TreeEntry = collections.namedtuple('TreeEntry', ['uukey', 'last_hashed'])
UukeyStorage = collections.namedtuple('UukeyStorage', [
    'multifile', # True/False
    'archive' # Archive ID
    ])

STORAGE_PLACEHOLDER = UukeyStorage(False, None)
STORAGE_PLACEHOLDER_MULTI = UukeyStorage(True, None)

class Tree(object):
    def __init__(self, **kwargs):
        # Map from file path to TreeEntry
        self.files = {}
        self.dirs = []
        # Map from file path to symlink target
        self.symlinks = {}
        # Map from uukey to storage location (UukeyStorage)
        self.uukey_to_storage = {}
        self.lastar = 0

        props_to_copy = ['files', 'dirs', 'symlinks', 'uukey_to_storage', 'lastar']
        for p in props_to_copy:
            if p in kwargs:
                self.__dict__[p] = kwargs[p]


    def copy(self):
        return Tree(
                files = self.files.copy(),
                dirs = self.dirs[:],
                symlinks = self.symlinks.copy(),
                uukey_to_storage = self.uukey_to_storage.copy(),
                lastar = self.lastar
                )

    def has_uukey(self, uukey):
        return uukey in self.uukey_to_storage


def load_tree(data):
    sio = stringio.StringIO(data)
    magic_str = sio.read(4)
    if magic_str != b'PFTR':
        raise RuntimeError("magic string not found")

    version_str = sio.read(4)
    version = struct.unpack("!I", version_str)[0]
    if version == TREE_VER_P1:
        return pickle.load(sio)
    else:
        raise RuntimeError("tree version not supported")

def save_tree(tree, fp):
    fp.write(b'PFTR')
    fp.write(struct.pack('!I', TREE_VER_P1))
    pickle.dump(tree, fp)

def print_tree(tree):
    for (path, te) in tree.files.items():
        print('{}:\n\t{}'.format(path, te))
        print()

    print(tree.uukey_to_storage)
    print(tree.num_to_id)
