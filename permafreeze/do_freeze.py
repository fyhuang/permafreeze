import os
import os.path
import sys
import stat
import errno
from datetime import datetime

from permafreeze import uukey_and_size, shorten, tree

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
        # Make sure the data is stored
        if old_entry.uukey in old_tree.hashes:
            if old_entry.last_hashed >= mtime_dt:
                return True
    except KeyError: # old_tree.files doesn't contain target_path
        pass

    return False


def do_freeze(cp, old_tree, root_path):
    if not os.path.isdir(root_path):
        print("WARNING: {} doesn't exist or is not a directory".format(root_path))
        return None

    dry_run = cp.getboolean('options', 'dry-run')


    new_tree = old_tree.copy()

    for (root, dirs, files) in os.walk(root_path):
        prefix = root[len(root_path):]
        for fn in files:
            full_path = os.path.join(root, fn)
            target_path = os.path.join(prefix, fn)
            sys.stdout.write('Processing {}... '.format(shorten(target_path)))
            sys.stdout.flush()
            
            if should_skip(cp, target_path, full_path, old_tree):
                print('I')
                continue

            if os.path.islink(full_path):
                # TODO
                print('NI')
                continue

            # Hash and check if data already stored
            uukey, file_size = uukey_and_size(full_path)
            store_data = False
            if uukey not in new_tree.hashes:
                store_data = True

            # Update tree and archive
            new_tree.files[target_path] = tree.TreeEntry(uukey, datetime.utcnow())
            if store_data:
                new_tree.hashes[uukey] = "archive-name"
                if cp.getboolean('options', 'dont-archive'):
                    print('H {}'.format(uukey[:32]))
                else:
                    raise NotImplementedError('Archiving not implemented yet')

            else:
                print('I')

    # Store the new tree
    return new_tree

