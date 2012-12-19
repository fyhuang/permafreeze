from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import sys
import time
import argparse

from datetime import datetime
import ConfigParser as configparser

import hasher

def uukey_and_size(filename):
    csum, size = hasher.hash_and_size(filename)
    return (csum + "{0:016x}".format(size), size)

def shorten(filename, maxlen=58):
    if len(filename) > maxlen:
        hm = maxlen // 2
        left = filename[:hm-3]
        right = filename[-hm:]
        return left + "..." + right
    else:
        return filename


from permafreeze import tree, archiver, storage
from permafreeze.do_freeze import do_freeze


def do_check(cp, old_tree, root_path, extra):
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

            uukey, file_size = uukey_and_size(full_path)
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


def process_all(cp, func, extra):
    targets = cp.options('targets')
    for t in targets:
        root_path = unicode(cp.get('targets', t))

        # Load old tree
        rsi = storage.get_stored_info(cp, t)
        old_tree = rsi.last_tree

        # Do action and save tree
        new_extra_dict = dict(extra, **{
            'target-name': t,
            })
        new_tree = func(cp, old_tree, root_path, new_extra_dict)

        if new_tree is not None and \
                not cp.getboolean('options', 'dry-run'):
            storage.save_tree(cp, t, new_tree)



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

            's3-pf-prefix': 'permafreeze-' + cp.get('options', 'site-name'),
            'glacier-pf-prefix': 'permafreeze site:{}'.format(cp.get('options', 'site-name')),
            }

    for (name, val) in opts.items():
        setq('options', name, val)

    setq('options', 'config-dir', DEFAULT_PF_CONFIG_DIR)
    if not os.path.isdir(cp.get('options', 'config-dir')):
        cdir = cp.get('options', 'config-dir')
        os.mkdir(cdir)
        os.mkdir(os.path.join(cdir, 'tmp'))


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

    # Do some sanity checks
    if len(cp.options('targets')) == 0:
        print("No targets set (edit your config file!)")
        sys.exit(1)

    if args.dry_run:
        cp.set('options', 'dry-run', True)

    # Run the actual command
    if args.command == 'freeze':
        process_all(cp, do_freeze, {})

    elif args.command == 'check':
        process_all(cp, do_check, {})
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


if __name__ == "__main__":
    main()
