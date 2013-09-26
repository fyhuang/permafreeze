"""
Terminology:
    - File, a file. Has uukey.
    - Tree, in-memory representation of filesystem tree
    - Pack, collection of small files. UUID starts with P
    - Storage Tag, a storage-specific identifier for a file or pack
"""

from __future__ import division, absolute_import, print_function, unicode_literals

import os
import os.path
import sys
import time
import errno
import shutil
import getpass
import argparse
import tempfile

from datetime import datetime
from StringIO import StringIO
from collections import namedtuple
import ConfigParser as configparser

# For DefaultHost
import boto.s3.connection

import libpf


def uukey_and_size(filename):
    csum, size = libpf.hash_and_size(filename)
    return (csum + "{0:016x}".format(size), size)


# From <http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python>
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def formatpath(filename, maxlen=48):
    if len(filename) > maxlen:
        hm = maxlen // 2
        left = filename[:hm-3]
        right = filename[-hm:]
        return left + "..." + right
    else:
        rest = maxlen - len(filename)
        return filename + (" "*rest)

def files_to_consider(conf, target_name):
    root_path = conf.get('targets', target_name)
    for (root, dirs, files) in os.walk(root_path):
        prefix = root[len(root_path):]
        if len(prefix) == 0:
            prefix = '/'

        for fn in files:
            full_path = os.path.join(root, fn)
            target_path = os.path.join(prefix, fn)
            # TODO: excludes, etc.
            yield (full_path, target_path)

        # TODO: dirs


class M_ProgressReport(namedtuple('M_ProgressReport', ['done', 'total'])):
    def __repr__(self):
        width = 50
        ratio = self.done / self.total

        sio = StringIO()
        sio.write('[')
        for i in range(width):
            cratio = i / width
            if cratio <= ratio:
                sio.write('#')
            else:
                sio.write(' ')
        sio.write("] {}%".format(ratio * 100))
        return sio.getvalue()


from permafreeze import tree, archiver, storage
from permafreeze.freeze import do_freeze


def process_all(cp, func, st, extra):
    targets = cp.options('targets')
    for t in targets:
        root_path = unicode(cp.get('targets', t))

        # Load old tree
        rsi = storage.newest_tree(cp, st, t)
        old_tree = rsi.last_tree

        # Do action and save tree
        new_extra_dict = dict(extra, **{
            'target-name': t,
            })
        new_tree = func(cp, old_tree, root_path, new_extra_dict)

        if new_tree is not None and \
                not cp.getboolean('options', 'dry-run'):
            st.save_tree(cp, t, new_tree)


DEFAULT_PF_CONFIG_DIR = os.path.expanduser('~/.config/permafreeze/')
DEFAULT_PF_CONFIG_FILE = os.path.join(DEFAULT_PF_CONFIG_DIR, "config.ini")
DEFAULT_FILESIZE_LIMIT = 16 * 1024 * 1024 # 16 MB

class PfConfig(configparser.SafeConfigParser):
    def getopt(self, name):
        return self.get('options', name)

    def set_default_options(self):
        # Set default options
        def setq(s, o, v):
            if not self.has_option(s, o):
                self.set(s, o, v)

        TEMPDIR_PATH = tempfile.mkdtemp('pf{}'.format(getpass.getuser()))

        opts = {'dry-run': 'False',
                'ignore-dotfiles': 'False',
                'ignore-config': 'True',
                'tree-only': 'False', # DANGEROUS: might be buggy
                'filesize-limit': str(DEFAULT_FILESIZE_LIMIT),
                'temp-dir': TEMPDIR_PATH,

                's3-host': boto.s3.connection.S3Connection.DefaultHost,
                's3-port': '443',
                's3-create-bucket': 'False',

                's3-pf-prefix': 'permafreeze-' + self.get('options', 'site-name'),
                'glacier-pf-prefix': 'permafreeze site:{}'.format(self.get('options', 'site-name')),
                }

        for (name, val) in opts.items():
            setq('options', name, val)

        # Temporary directories
        self.default_tempdir = self.getopt('temp-dir') == TEMPDIR_PATH
        if not self.default_tempdir:
            # We need to remove the tempdir that we created
            os.rmdir(TEMPDIR_PATH)

        if not self.has_option('options', 'cache-dir'):
            # TODO: should cache dir be persistent?
            self.set('options', 'cache-dir',
                     os.path.join(self.getopt('temp-dir'), 'cache'))
            if not os.path.isdir(self.getopt('cache-dir')):
                os.mkdir(self.getopt('cache-dir'))

    def set_defaults(self):
        self.set_default_options()

        # Setup default components
        self.st = storage.AmazonStorage(self)

    def tempdir(self, name, create=True):
        tmpdir_path = os.path.join(self.getopt('temp-dir'), name)
        if create and not os.path.isdir(tmpdir_path):
            mkdir_p(tmpdir_path)
        return tmpdir_path

    def cleanup(self):
        """Removes temporary directory if it is the default one. Idempotent."""
        if self.default_tempdir and os.path.isdir(self.getopt('temp-dir')):
            shutil.rmtree(self.getopt('temp-dir'))

    # Support for with statement
    def __enter__(self):
        return self
    def __exit__(self, extype, exvalue, extb):
        self.cleanup()

def load_config(config_filename):
    if not os.path.isfile(config_filename):
        if config_filename == DEFAULT_PF_CONFIG_FILE:
            # TODO: copy over the default config file
            print("TODO: copy over the default config file")
            sys.exit(1)
        else:
            print("Config file {} doesn't exist".format(config_filename))
            sys.exit(1)

    cp = PfConfig()
    cp.read(config_filename)
    return cp



def main():
    args = parse_args()

    cp = load_config(args.config)

    # Do some sanity checks
    if len(cp.get('options', 'site-name')) == 0:
        print("No site-name set (edit your config file!)")
        sys.exit(1)
    if len(cp.options('targets')) == 0:
        print("No targets set (edit your config file!)")
        sys.exit(1)

    if args.dry_run:
        cp.set('options', 'dry-run', 'True')
    if args.hash_only:
        cp.set('options', 'dont-archive', 'True')

    cp.set_defaults()

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
    aparser.add_argument('-H', '--hash-only', action='store_true')

    return aparser.parse_args()


if __name__ == "__main__":
    main()
