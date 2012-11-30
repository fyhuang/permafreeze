from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import sys
import time

from datetime import datetime
import ConfigParser as configparser

import hasher
from permafreeze import tree


def cp_getboolean_d(cp, section, option, default):
    try:
        return cp.getboolean(section, option)
    except configparser.NoOptionError:
        return default

def do_check(cp, old_tree, root_path):
    if not os.path.isdir(root_path):
        print("WARNING: {} doesn't exist or is not a directory".format(root_path))

    ignore_dotfiles = cp_getboolean_d(cp, 'options', 'ignore-dotfiles', False)

    total_files = 0
    skipped_files = 0
    errors = []
    for (root, dirs, files) in os.walk(root_path):
        prefix = root[len(root_path):]
        for fn in files:
            if ignore_dotfiles and fn[0] == '.':
                continue

            full_path = os.path.join(root, fn)
            target_path = os.path.join(prefix, fn)
            if os.path.islink(full_path):
                # TODO
                continue

            total_files += 1
            if total_files % 100 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()
            mtime_dt = datetime.utcfromtimestamp(os.path.getmtime(full_path))
            check = True
            try:
                old_entry = old_tree.files[target_path]
                if old_entry.last_hashed < mtime_dt:
                    check = False
            except KeyError:
                check = False

            if not check:
                skipped_files += 1
                continue

            uukey = hasher.file_unique_key(full_path)
            if uukey != old_entry.uukey:
                print("WARNING: hash mismatch! {}".format(target_path))
                errors.append(target_path)

    print()
    print("Finished consistency check:")
    print("{} files on disk ({} skipped), {} in tree".format(total_files, skipped_files, len(old_tree.files)))
    print("{} errors".format(len(errors)))
    for e in errors:
        print(e)


def do_freeze(cp, old_tree, root_path):
    if not os.path.isdir(root_path):
        print("WARNING: {} doesn't exist or is not a directory".format(root_path))

    ignore_dotfiles = cp_getboolean_d(cp, 'options', 'ignore-dotfiles', False)
    dry_run = cp_getboolean_d(cp, 'options', 'dry-run', False)


    new_tree = old_tree.copy()

    for (root, dirs, files) in os.walk(root_path):
        prefix = root[len(root_path):]
        for fn in files:
            if ignore_dotfiles and fn[0] == '.':
                continue

            full_path = os.path.join(root, fn)
            target_path = os.path.join(prefix, fn)
            if os.path.islink(full_path):
                # TODO
                pass
            else:
                uukey = hasher.file_unique_key(full_path)

            store = False
            if uukey not in new_tree.hashes:
                store = True

            new_tree.files[target_path] = tree.TreeEntry(uukey, datetime.utcnow())
            if store:
                print("Storing {} ({})".format(target_path, uukey))
                new_tree.hashes[uukey] = "archive-name"
                # TODO
            else:
                print("Skipping {}".format(target_path))

    # Store the new tree
    return new_tree

def process_all(cp, func):
    targets = cp.options('targets')
    for t in targets:
        root_path = cp.get('targets', t)

        # Load old tree
        if os.path.isfile(t+'-tree'):
            with open(t+'-tree', 'rb') as f:
                old_tree = tree.load_tree(f.read())
        else:
            old_tree = tree.Tree({}, {})

        new_tree = func(cp, old_tree, root_path)
        if new_tree is not None:
            with open(t+'-tree', 'wb') as f:
                tree.save_tree(new_tree, f)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    cp = configparser.SafeConfigParser()
    cp.read(argv[1])
    if len(argv) >= 3 and argv[2] == "-n":
        cp.set('options', 'dry-run', True)

    process_all(cp, do_freeze)
