from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import errno
import sys
import shutil
import tarfile
from contextlib import closing

from permafreeze import formatpath, mkdir_p
from permafreeze.logger import log
from permafreeze.messages import StartedProcessingFile, ProcessFileResult
from permafreeze.tree import TreeEntry, FileEntry, SymlinkEntry

def uukeys_and_archives(tree):
    result = []
    for (relpath, entry) in tree.files.items():
        arnum = tree.uukey_to_arnum[entry.uukey]
        arid = tree.num_to_id[arnum]
        result.append((relpath, entry.uukey, arid))
    result.sort(key=lambda e: e[2])
    return result

def thaw_file(conf, tree, entry, fullpath):
    assert(isinstance(entry, FileEntry))
    # TODO: posix stuff
    utype = tree.uuid_type(entry.uuid)
    if utype == 'smallfile':
        # Small file
        pack_id = tree.file_pack[entry.uuid]
        data_cf = conf.st.load_archive(tree.uuid_to_storage[pack_id])
        archive = tarfile.open(data_cf.fullpath(), 'r')
        with closing(archive):
            inf = archive.extractfile(entry.uuid)

            with closing(inf), open(fullpath, 'wb') as outf:
                shutil.copyfileobj(inf, outf)
                log(ProcessFileResult('OK'))
    else:
        storage_tag = tree.uuid_to_storage[entry.uuid]
        data_cf = conf.st.load_archive(storage_tag)
        with closing(data_cf):
            shutil.copy(data_cf.fullpath(), fullpath)
            log(ProcessFileResult('OK'))

def thaw_symlink(entry, fullpath):
    assert(isinstance(entry, SymlinkEntry))
    # TODO: windows?
    starget = entry.symlink_target
    try:
        os.symlink(starget, fullpath)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.islink(fullpath):
            pass
        else: raise

    log(ProcessFileResult('OK'))

def do_thaw(conf, tree, dest_path):
    """st: the storage object to pull archives from"""

    for (relpath, entry) in tree.entries.items():
        fullpath = os.path.join(dest_path, relpath.lstrip('/'))
        log(StartedProcessingFile(relpath, fullpath))

        dirname = os.path.dirname(fullpath)
        # Sanity check
        assert dest_path.rstrip('/') in dirname

        mkdir_p(dirname)

        # Check type of entry
        if entry.entry_type == TreeEntry.FILE:
            thaw_file(conf, tree, entry, fullpath)
        elif entry.entry_type == TreeEntry.DIR:
            # TODO: perms
            os.mkdir(fullpath)
        elif entry.entry_type == TreeEntry.SYMLINK:
            thaw_symlink(entry, fullpath)
        else:
            raise NotImplementedError("TreeEntry type not recognized: {}".format(entry.entry_type))
