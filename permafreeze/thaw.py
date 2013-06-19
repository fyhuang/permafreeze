from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import errno
import shutil
from contextlib import closing

from permafreeze import formatpath

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

        fullpath = os.path.join(dest_path, relpath.lstrip('/'))
        dirname = os.path.dirname(fullpath)
        # Sanity check
        assert dest_path.rstrip('/') in dirname

        mkdir_p(dirname)

        arnum = tree.uukey_to_arnum[entry.uukey]
        archive_id = tree.num_to_id[arnum]
        archive = st.load_archive(cp, archive_id)
        with closing(archive):
            inf = archive.extractfile(entry.uukey)

            with closing(inf), open(fullpath, 'wb') as outf:
                shutil.copyfileobj(inf, outf)
                print("OK")
