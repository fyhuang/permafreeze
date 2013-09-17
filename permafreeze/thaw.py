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

def do_thaw(conf, tree, dest_path):
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

        storage_id = tree.uuid_to_storage[entry.uuid]
        data_cf = st.load_archive(storage_id)
        with closing(data_cf):
            utype = tree.uuid_type(entry.uukey)
            if utype == 'smallfile':
                archive = tarfile.open(data_cf.fullpath(), 'r')
                with closing(archive):
                    inf = archive.extractfile(entry.uukey)

                    with closing(inf), open(fullpath, 'wb') as outf:
                        shutil.copyfileobj(inf, outf)
                        print("OK")
            else:
                shutil.copy(data_cf.fullpath(), fullpath)
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
