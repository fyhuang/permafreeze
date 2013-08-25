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

from permafreeze import uukey_and_size, formatpath, print_progress
from permafreeze import tree, archiver

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
    if cp.getboolean('options', 'ignore-dotfiles'):
        if os.path.basename(full_path)[0] == '.':
            return True

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

    mtime_dt = datetime.utcfromtimestamp(sb.st_mtime)
    try:
        old_entry = old_tree.files[target_path]
        if old_entry.last_hashed is None:
            # Never been hashed
            return False

        # Make sure the data is stored
        if old_entry.uukey in old_tree.hashes:
            if old_entry.last_hashed >= mtime_dt:
                return True
    except KeyError: # old_tree.files doesn't contain target_path
        pass

    return False

def iter_files(cp, target_root_path, old_tree):
    for (root, dirs, files) in os.walk(target_root_path):
        prefix = root[len(target_root_path):]
        if len(prefix) == 0:
            prefix = '/'

        for fn in files:
            full_path = os.path.join(root, fn)
            target_path = os.path.join(prefix, fn)

            print(formatpath(target_path), end="")
            sys.stdout.flush()
            
            if should_skip(cp, target_path, full_path, old_tree):
                print('Skip')
                continue

            yield (full_path, target_path)


def do_freeze(cp, old_tree, root_path, ar, extra):
    if not os.path.isdir(root_path):
        print("WARNING: {} doesn't exist or is not a directory".format(root_path))
        return None

    dry_run = cp.getboolean('options', 'dry-run')
    new_tree = old_tree.copy()
    small_uukeys = {}
    uploader = FileUploader(cp, ar.extstorage)
    uploader.start()

    def store_file_small(full_path, uukey, target_path):
        if not dry_run: 
            ar.add_file(full_path, uukey, file_size)
        new_tree.uukey_to_storage[uukey] = tree.STORAGE_PLACEHOLDER_MULTI
        small_uukeys[uukey] = ar.curr_num

    def store_file_large(full_path, uukey, target_path):
        if not dry_run:
            # Uploads to Glacier in another thread
            uploader.store(full_path, uukey)
        new_tree.uukey_to_storage[uukey] = tree.STORAGE_PLACEHOLDER

    def store_archive(ar_uuid, arpath):
        if not dry_run:
            uploader.store(arpath, ar_uuid)
        new_tree.uukey_to_storage[ar_uuid] = tree.STORAGE_PLACEHOLDER

    def store_symlink(full_path, target_path):
        symlink_target = os.path.realpath(full_path)
        if symlink_target.startswith(root_path):
            symlink_target = os.path.relpath(symlink_target, os.path.dirname(full_path))

        new_tree.symlinks[target_path] = symlink_target



    for (full_path, target_path) in iter_files(cp, root_path, old_tree):
        # Symlinks
        if os.path.islink(full_path):
            store_symlink(full_path, target_path)
            print('OK')
            continue

        # Hash and check if data already stored
        uukey, file_size = uukey_and_size(full_path)
        if cp.getboolean('options', 'tree-only'):
            new_tree.files[target_path] = tree.TreeEntry(uukey, None)
            print('{}'.format(uukey[:32]))
            continue


        new_tree.files[target_path] = tree.TreeEntry(uukey, datetime.utcnow())
        if not new_tree.has_uukey(uukey):
            if file_size <= cp.getint('options', 'filesize-limit'):
                store_file_small(full_path, uukey, target_path)
            else:
                store_file_large(full_path, uukey, target_path)
            print('{}'.format(uukey[:32]))
        else:
            print('OK')


    # Update archive IDs
    ar.finish_archive()
    uploader.to_store.put('Done')
    new_tree.lastar = ar.curr_num

    for (uukey, arnum) in small_uukeys.items():
        if new_tree.uukey_to_storage[uukey] != tree.STORAGE_PLACEHOLDER_MULTI:
            print("ERROR: uukey {} already has storage".format(uukey))
            continue

        new_tree.uukey_to_storage[uukey] = tree.UukeyStorage(True, ar.num_to_id[arnum])

    # Progress indicator
    print("\nWaiting for uploads to complete")
    while True:
        num_processed = uploader.progress.get()
        print_progress(num_processed / uploader.num_requested)
        if num_processed == uploader.num_requested:
            break
    print()

    uploader.join()

    try:
        for i in range(uploader.num_requested):
            (uukey, archiveid) = uploader.done.get(False)
            new_tree.uukey_to_storage[uukey] = tree.UukeyStorage(False, archiveid)
    except queue.Empty:
        print("ERROR: not enough processed files")

    if not uploader.done.empty():
        print("ERROR: some files unaccounted!")

    # Store the new tree
    return new_tree

