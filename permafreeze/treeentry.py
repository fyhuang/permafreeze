from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future import standard_library
from future.builtins import *

from collections import namedtuple

class TreeEntry(object):
    FILE = 0
    DIR = 1
    SYMLINK = 2

    def __init__(self, entry_type, posix_uid, posix_gid, posix_perms):
        self.entry_type = entry_type
        self.posix_uid = posix_uid
        self.posix_gid = posix_gid
        self.posix_perms = posix_perms

class FileEntry(TreeEntry):
    def __init__(self, posix_uid, posix_gid, posix_perms, uuid, last_hashed):
        super().__init__(TreeEntry.FILE,
            posix_uid, posix_gid, posix_perms)
        self.uuid = uuid
        self.last_hashed = last_hashed

class SymlinkEntry(TreeEntry):
    def __init__(self, symlink_target):
        super().__init__(TreeEntry.SYMLINK,
            0, 0, 0)
        self.symlink_target = symlink_target
