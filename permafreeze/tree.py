from __future__ import division, absolute_import, print_function, unicode_literals

import struct
import pickle
import collections
import StringIO as stringio

TREE_VER_P1 = 0

TreeEntry = collections.namedtuple('TreeEntry', ['uukey', 'last_hashed'])

class Tree(object):
    def __init__(self, files={}, uukey_to_arnum={}, lastar=0, num_to_id={}):
        # Map from file path to TreeEntry
        self.files = files
        # Map from uukey to archive number
        self.uukey_to_arnum = uukey_to_arnum
        self.lastar = lastar
        self.num_to_id = num_to_id

    def copy(self):
        return Tree(self.files.copy(), self.uukey_to_arnum.copy(), self.lastar, self.num_to_id)


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

    print(tree.uukey_to_arnum)
    print(tree.num_to_id)
