from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import sys
import stat
import errno

from datetime import datetime
from contextlib import closing
from multiprocessing import Queue, Process
import Queue as queue

from permafreeze import uukey_and_size, formatpath, files_to_consider
from permafreeze import tree, archiver
from permafreeze.logger import log
from permafreeze.messages import StartedProcessingFile, ProcessFileResult, ProgressReport


class FileUploader(object):
    def __init__(self, cp, st):
        self.to_store = Queue()
        self.done = Queue()
        self.progress = Queue()
        self.num_requested = 0

        self.cp = cp
        self.st = st

    @staticmethod
    def _run(self):
        num_processed = 0
        while True:
            nextitem = self.to_store.get()
            if isinstance(nextitem, unicode) and nextitem == 'Done':
                break

            full_path, uukey = nextitem
            aid = self.st.save_archive(full_path)

            self.done.put((uukey, aid))
            num_processed += 1
            self.progress.put(num_processed)

    def start(self):
        self.proc = Process(target=FileUploader._run, args=(self,))
        self.proc.start()

    def join(self):
        self.proc.join()

    def store(self, full_path, uukey):
        self.to_store.put((full_path, uukey))
        self.num_requested += 1


def should_skip(cp, target_path, full_path, old_tree):
    try:
        sb = os.stat(full_path)
        if not stat.S_ISREG(sb.st_mode) and \
                not stat.S_ISLNK(sb.st_mode):
            # Non-regular file or link
            return True
    except OSError as e:
        if e.errno == errno.ENOENT or \
                e.errno == errno.EPERM:
            return True

    # TODO: UTC or not?
    mtime_dt = datetime.utcfromtimestamp(sb.st_mtime)
    try:
        old_entry = old_tree.files[target_path]
        if old_entry.last_hashed is None:
            # Never been hashed
            return False

        # Make sure the data is stored
        if old_tree.is_stored(old_entry.uuid):
            if old_entry.last_hashed >= mtime_dt:
                return True
    except KeyError: # old_tree.files doesn't contain target_path
        pass

    return False


def do_freeze(cp, old_tree, target_name):
    if not cp.has_option('targets', target_name):
        print("ERROR: target {} doesn't exist".format(target_name))
        return None

    dry_run = cp.getboolean('options', 'dry-run')
    new_tree = old_tree.copy()
    uploader = FileUploader(cp, cp.st)
    uploader.start()

    def store_file_small(full_path, uukey, target_path):
        uuid = None
        if not dry_run: 
            uuid = ar.add_file(full_path, uukey, file_size)
        new_tree.file_pack[uukey] = uuid

    def store_file_large(full_path, uukey, target_path):
        if not dry_run:
            # Uploads to Glacier in another thread
            uploader.store(full_path, uukey)
        new_tree.uuid_to_storage[uukey] = None

    def store_archive(ar_uuid, arpath):
        if not dry_run:
            uploader.store(arpath, ar_uuid)
        new_tree.uuid_to_storage[ar_uuid] = None

    def store_symlink(full_path, target_path):
        symlink_target = os.path.realpath(full_path)
        if symlink_target.startswith(root_path):
            symlink_target = os.path.relpath(symlink_target, os.path.dirname(full_path))

        new_tree.symlinks[target_path] = symlink_target


    root_path = cp.get('targets', target_name)
    ar = archiver.Archiver(cp, target_name)
    ar.set_callback(store_archive)

    # TODO: Use files_to_consider
    for (full_path, target_path) in files_to_consider(cp, target_name):
        log(StartedProcessingFile(target_path, full_path))

        # Should we skip this file?
        if should_skip(cp, target_path, full_path, old_tree):
            log(ProcessFileResult('Skip'))
            continue

        # Symlinks
        if os.path.islink(full_path):
            store_symlink(full_path, target_path)
            log(ProcessFileResult('Symlink'))
            continue

        # Hash and check if data already stored
        uukey, file_size = uukey_and_size(full_path)
        if cp.getboolean('options', 'tree-only'):
            new_tree.files[target_path] = tree.TreeEntry(uukey, None)
            log(ProcessFileResult('{}'.format(uukey[:32])))
            continue


        new_tree.files[target_path] = tree.TreeEntry(uukey, datetime.utcnow())
        if not new_tree.is_stored(uukey):
            if file_size <= cp.getint('options', 'filesize-limit'):
                store_file_small(full_path, uukey, target_path)
            else:
                store_file_large(full_path, uukey, target_path)
            log(ProcessFileResult('{}'.format(uukey[:32])))
        else:
            print('ERROR: should be skipped')


    # Update archive IDs
    ar.finish_archive()
    uploader.to_store.put('Done')

    # Progress indicator
    while True:
        num_processed = uploader.progress.get()
        log(ProgressReport(num_processed, uploader.num_requested))
        if num_processed == uploader.num_requested:
            break
    uploader.join()

    # Resolve archive IDs
    try:
        for i in range(uploader.num_requested):
            (uuid, storageid) = uploader.done.get(False)
            new_tree.uuid_to_storage[uuid] = storageid
    except queue.Empty:
        print("ERROR: not enough processed files")

    if not uploader.done.empty():
        print("ERROR: some files unaccounted!")

    # Check to see that all UUIDs in tree have storage tag
    for uuid, stag in new_tree.uuid_to_storage.items():
        if stag is None:
            print("ERROR: uuid {} doesn't have storage tag".format(uuid))

    # Store the new tree
    return new_tree

