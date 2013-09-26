from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import weakref
import collections

from permafreeze import mkdir_p

class CachedFile(object):
    def __init__(self, filename, cache):
        self.filename = filename
        self.cache = weakref.ref(cache)
        self.active = True

    def __del__(self):
        self.close()

    def close(self):
        if self.active:
            self.cache()._notify_inactive(self)
        self.active = False

    def fullpath(self):
        return os.path.join(self.cache().cachedir, self.filename)

class FileCache(object):
    def __init__(self, cp,
            # 512 MB
            maxsize = 512 * 1024 * 1024):

        self.refcount = {} # filename to refcount
        self.can_delete = collections.deque()

        self.cp = cp
        self.cachedir = cp.getopt('cache-dir')
        self.maxsize = maxsize

        # TODO: scan existing cached files?

    def _notify_inactive(self, cf):
        self.refcount[cf.filename] -= 1
        if self.refcount[cf.filename] == 0:
            self.can_delete.append(cf.filename)
        elif self.refcount[cf.filename] < 0:
            raise RuntimeError("FileCache: refcount error")

    def compute_size(self):
        total_size = 0
        for (root, dirs, files) in os.walk(self.cachedir):
            for fn in files:
                total_size += os.path.getsize(os.path.join(root, fn))
        return total_size

    def hasfile(self, filename):
        return filename in self.refcount and self.refcount[filename] > 0

    def getfile(self, filename):
        if filename in self.refcount:
            self.refcount[filename] += 1
            return CachedFile(filename, self)
        else:
            raise KeyError()

    def newfile(self, filename):
        if filename in self.refcount and self.refcount[filename] > 0:
            raise Exception("newfile: already exists")

        # Check if max size is over
        if self.compute_size() > self.maxsize:
            self.cleanup()

        self.refcount[filename] = 1
        return CachedFile(filename, self)

    def cleanup(self):
        while len(self.can_delete) > 0:
            fn = self.can_delete.popleft()
            if fn in self.refcount:
                if self.refcount[fn] > 0:
                    continue
                del self.refcount[fn]

            try:
                full_fn = os.path.join(self.cachedir, fn)
                os.remove(full_fn)
            except OSError:
                continue

