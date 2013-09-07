from __future__ import division, absolute_import, print_function, unicode_literals

import copy
import struct
import pickle
import datetime
import collections
import StringIO as stringio

TREE_VER_P1 = 1

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
        self.dirs = [] # TODO
        # Map from file path to symlink target
        self.symlinks = {}
        # Map from uukey to storage location (UukeyStorage)
        self.uukey_to_storage = {}
        self.generated_dt = None

        props_to_copy = ['files', 'dirs', 'symlinks', 'uukey_to_storage', 'generated_dt']
        for p in props_to_copy:
            if p in kwargs:
                self.__dict__[p] = kwargs[p]


    def copy(self):
        return Tree(
                files = self.files.copy(),
                dirs = self.dirs[:],
                symlinks = self.symlinks.copy(),
                uukey_to_storage = self.uukey_to_storage.copy(),
                generated_dt = copy.copy(self.generated_dt)
                )

    def has_uukey(self, uukey):
        return uukey in self.uukey_to_storage


def tree_from_str(data):
    sio = stringio.StringIO(data)
    magic_str = sio.read(4)
    if magic_str != b'PFTR':
        raise RuntimeError("magic string not found")

    version_str = sio.read(4)
    version = struct.unpack("!I", version_str)[0]
    if version != TREE_VER_P1:
        raise RuntimeError("tree version not supported")

    return pickle.load(sio)

def save_tree(tree_to_save, fp):
    fp.write(b'PFTR')
    fp.write(struct.pack(b'!I', TREE_VER_P1))
    pickle.dump(tree_to_save, fp)

def print_tree(tree):
    for (path, te) in tree.files.items():
        print('{}:\n\t{}'.format(path, te))
        print()

    print(tree.uukey_to_storage)
    print(tree.dirs)
    print(tree.symlinks)
