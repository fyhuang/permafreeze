from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future import standard_library
from future.builtins import *

import copy
import struct
import pickle
import datetime
import collections
from io import StringIO

from permafreeze.treeentry import *

TREE_VER_P1 = 1

class Tree(object):
    def __init__(self, **kwargs):
        # Map from file path to TreeEntry
        self.entries = {}

        # Map from uukey to pack
        self.file_pack = {}
        # Map from uuid to storage tag
        self.uuid_to_storage = {}
        self.generated_dt = None

        props_to_copy = ['entries', 'file_pack', 'uuid_to_storage', 'generated_dt']
        for p in props_to_copy:
            if p in kwargs:
                self.__dict__[p] = kwargs[p]


    def copy(self):
        return Tree(
                entries = self.entries.copy(),
                file_pack = self.file_pack.copy(),
                uuid_to_storage = self.uuid_to_storage.copy(),
                generated_dt = copy.copy(self.generated_dt)
                )

    def is_stored(self, uuid):
        if uuid in self.file_pack:
            return True
        if uuid in self.uuid_to_storage:
            return True
        return False

    def uuid_type(self, uuid):
        if uuid in self.file_pack:
            return 'smallfile'
        elif uuid in self.uuid_to_storage:
            if uuid[0] == 'P':
                return 'pack'
            else:
                return 'largefile'
        else:
            return None


def tree_from_str(data):
    sio = StringIO(data)
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
    for (path, te) in tree.entries.items():
        print('{}:\n\t{}'.format(path, te))
        print()

    print(tree.file_pack)
    print(tree.uuid_to_storage)
