import struct
import pickle
import collections
import StringIO as stringio

TREE_VER_P1 = 0

TreeEntry = collections.namedtuple('TreeEntry', ['uukey', 'last_hashed'])

class Tree(object):
    def __init__(self, files, hashes):
        self.files = files
        self.hashes = hashes

    def copy(self):
        return Tree(self.files.copy(), self.hashes.copy())


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
