from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import sys
import time
import argparse

from datetime import datetime
import ConfigParser as configparser

import hasher
from permafreeze import tree


def do_check(cp, old_tree, root_path):
    total_files = 0
    skipped_files = 0
    errors = []

    if len(old_tree.files) == 0 and len(old_tree.hashes) == 0:
        errors.append("No stored tree for {}".format(root_path))
    if not os.path.isdir(root_path):
        errors.append("{} doesn't exist or is not a directory".format(root_path))

    for (root, dirs, files) in os.walk(root_path):
        prefix = root[len(root_path):]
        for fn in files:
            if cp.getboolean('options', 'ignore-dotfiles') and \
                    fn[0] == '.':
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
    print()
    if len(errors) > 0:
        print("{} errors:".format(len(errors)))
        for e in errors:
            print(e)
    else:
        print("No errors.")


def do_freeze(cp, old_tree, root_path):
    if not os.path.isdir(root_path):
        print("WARNING: {} doesn't exist or is not a directory".format(root_path))
        return None

    dry_run = cp.getboolean('options', 'dry-run')


    new_tree = old_tree.copy()

    for (root, dirs, files) in os.walk(root_path):
        prefix = root[len(root_path):]
        for fn in files:
            if cp.getboolean('options', 'ignore-dotfiles') and \
                    fn[0] == '.':
                continue

            full_path = os.path.join(root, fn)
            target_path = os.path.join(prefix, fn)
            if os.path.islink(full_path):
                # TODO
                continue

            # Skip if not modified since last hashed
            mtime_dt = datetime.utcfromtimestamp(os.path.getmtime(full_path))
            try:
                old_entry = old_tree.files[target_path]
                # Make sure the data is stored
                if old_entry.uukey in old_tree.hashes:
                    if old_entry.last_hashed >= mtime_dt:
                        continue
            except KeyError:
                pass

            # Hash and check if data already stored
            uukey = hasher.file_unique_key(full_path)
            store_data = False
            if uukey not in new_tree.hashes:
                store_data = True

            # Update tree and archive
            new_tree.files[target_path] = tree.TreeEntry(uukey, datetime.utcnow())
            if store_data:
                print("Storing {} ({})".format(target_path, uukey))
                new_tree.hashes[uukey] = "archive-name"
                if cp.getboolean('options', 'dont-archive'):
                    pass
                else:
                    raise NotImplementedError('Archiving not implemented yet')

            else:
                print("Skipping {}".format(target_path))

    # Store the new tree
    return new_tree

def process_all(cp, func):
    targets = cp.options('targets')
    for t in targets:
        root_path = cp.get('targets', t)

        # Load old tree
        tree_local_fname = os.path.join(cp.get('options', 'config-dir'), 'tree-'+t)
        if os.path.isfile(tree_local_fname):
            with open(tree_local_fname, 'rb') as f:
                old_tree = tree.load_tree(f.read())
        else:
            old_tree = tree.Tree()

        # Do action and save tree
        new_tree = func(cp, old_tree, root_path)
        if new_tree is not None and \
                not cp.getboolean('options', 'dry-run'):
            with open(tree_local_fname, 'wb') as f:
                tree.save_tree(new_tree, f)



DEFAULT_PF_CONFIG_DIR = os.path.expanduser('~/.config/permafreeze/')
DEFAULT_PF_CONFIG_FILE = os.path.join(DEFAULT_PF_CONFIG_DIR, "config.ini")

def set_default_options(cp):
    def setq(s, o, v):
        if not cp.has_option(s, o):
            cp.set(s, o, v)

    opts = {'dry-run': 'False',
            'ignore-dotfiles': 'False',
            'ignore-config': 'True',
            'dont-archive': 'False', # DANGEROUS
            }

    for (name, val) in opts.items():
        setq('options', name, val)

    setq('options', 'config-dir', DEFAULT_PF_CONFIG_DIR)
    if not os.path.isdir(cp.get('options', 'config-dir')):
        os.mkdir(cp.get('options', 'config-dir'))


def main():
    args = parse_args()

    if not os.path.isfile(args.config):
        if args.config == DEFAULT_PF_CONFIG_FILE:
            # TODO: copy over the default config file
            sys.exit(1)
        else:
            print("Config file {} doesn't exist".format(args.config))
            sys.exit(1)

    cp = configparser.SafeConfigParser()
    cp.read(args.config)
    set_default_options(cp)

    if args.dry_run:
        cp.set('options', 'dry-run', True)

    if args.command == 'freeze':
        process_all(cp, do_freeze)
    elif args.command == 'check':
        process_all(cp, do_check)
    else:
        print("Command not recognized: {}".format(args.command))
        sys.exit(1)

def parse_args():
    aparser = argparse.ArgumentParser(description="permafreeze")
    aparser.add_argument('command', type=str, default='freeze', nargs='?')
    aparser.add_argument('-c', '--config',
            type=str,
            default=DEFAULT_PF_CONFIG_FILE)
    aparser.add_argument('-n', '--dry-run', action='store_true')

    return aparser.parse_args()

