from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import sys
import errno
import shutil
import tarfile
from contextlib import closing

from permafreeze import formatpath

def uukeys_and_archives(tree):
    result = []
    for (relpath, entry) in tree.files.items():
        arnum = tree.uukey_to_arnum[entry.uukey]
        arid = tree.num_to_id[arnum]
        result.append((relpath, entry.uukey, arid))
    result.sort(key=lambda e: e[2])
    return result

# From <http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python>
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def do_thaw(cp, tree, dest_path, st):
    """st: the storage object to pull archives from"""

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
        archive_filename = st.load_archive(cp, archive_id)
        if us.multifile:
            archive = tarfile.open(archive_filename, 'r')
            with closing(archive):
                inf = archive.extractfile(entry.uukey)

                with closing(inf), open(fullpath, 'wb') as outf:
                    shutil.copyfileobj(inf, outf)
                    print("OK")
        else:
            shutil.copy(archive_filename, fullpath)
            print("OK")
