from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import errno
import sys
import shutil
import tarfile
from contextlib import closing

from permafreeze import formatpath, mkdir_p

def uukeys_and_archives(tree):
    result = []
    for (relpath, entry) in tree.files.items():
        arnum = tree.uukey_to_arnum[entry.uukey]
        arid = tree.num_to_id[arnum]
        result.append((relpath, entry.uukey, arid))
    result.sort(key=lambda e: e[2])
    return result

def do_thaw(cp, tree, dest_path, st):
    """st: the storage object to pull archives from"""

    # Files
    for (relpath, entry) in tree.files.items():
        print(formatpath(relpath), end="")
        sys.stdout.flush()

        fullpath = os.path.join(dest_path, relpath.lstrip('/'))
        dirname = os.path.dirname(fullpath)
        # Sanity check
        assert dest_path.rstrip('/') in dirname

        mkdir_p(dirname)

        us = tree.uukey_to_storage[entry.uukey]
        archive_id = us.archive
        archive_cf = st.load_archive(archive_id)
        with closing(archive_cf):
            if us.multifile:
                archive = tarfile.open(archive_cf.fullpath(), 'r')
                with closing(archive):
                    inf = archive.extractfile(entry.uukey)

                    with closing(inf), open(fullpath, 'wb') as outf:
                        shutil.copyfileobj(inf, outf)
                        print("OK")
            else:
                shutil.copy(archive_cf.fullpath(), fullpath)
                print("OK")

    # Symlinks
    for (spath, starget) in tree.symlinks.items():
        print(formatpath(spath), end="")
        sys.stdout.flush()

        fullpath = os.path.join(dest_path, spath.lstrip('/'))
        dirname = os.path.dirname(fullpath)
        # Sanity check
        assert dest_path.rstrip('/') in dirname

        mkdir_p(dirname)

        # TODO: windows?
        try:
            os.symlink(starget, fullpath)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.islink(fullpath):
                pass
            else: raise

        print("OK")
