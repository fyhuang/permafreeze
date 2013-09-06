from __future__ import division, absolute_import, print_function, unicode_literals

import re
import os.path
from StringIO import StringIO
from datetime import datetime

from boto.s3.connection import S3Connection, Key, OrdinaryCallingFormat
from boto.glacier import layer2, vault

from permafreeze import tree
from permafreeze.storage import RemoteStoredInfo, FileCache

TREENAME_REGEX = re.compile(r"(?P<targetname>.+)\.(?P<dt>\d{8}T\d{4})")

class AmazonStorage(object):
    def __init__(self, cp):
        self.cp = cp
        self.cache = FileCache(cp)
        self.connected = False

        self.s3_conn = None
        self.s3_bucket = None
        self.gl_conn = None
        self.gl_vault = None

    def connect(self):
        if not self.connected:
            self.s3_conn = S3Connection(
                    self.cp.get('auth', 'accessKeyId'),
                    self.cp.get('auth', 'secretAccessKey'),
                    port=int(self.cp.get('options', 's3-port')),
                    host=self.cp.get('options', 's3-host'),
                    is_secure=False,
                    calling_format=OrdinaryCallingFormat(),
                    )

            s3bn = self.cp.get('options', 's3-bucket-name')
            self.s3_bucket = self.s3_conn.lookup(s3bn)
            if self.s3_bucket is None:
                if self.cp.getboolean('options', 's3-create-bucket'):
                    print("Creating S3 bucket")
                    self.s3_conn.create_bucket(s3bn)
                    self.s3_bucket = self.s3_conn.get_bucket(s3bn)
                else:
                    raise KeyError() # TODO

            '''
            self.gl_conn = layer2.Layer2(
                    aws_access_key_id=cp.get('auth', 'accessKeyId'),
                    aws_secret_access_key=cp.get('auth', 'secretAccessKey')
                    )
            self.gl_vault = self.gl_conn.create_vault(cp.get('options', 'glacier-vault-name')) # Idempotent
            '''

            self.connected = True
            print("Connected to Amazon S3")
            

    def newest_stored_tree(self, target):
        self.connect()

        s3_pf_prefix = self.cp.get('options', 's3-pf-prefix')

        all_s3_trees = self.s3_bucket.list(s3_pf_prefix + '/trees/')
        s3_trees_with_dt = []
        for t in all_s3_trees:
            basename = os.path.basename(t.key)
            m = TREENAME_REGEX.match(basename)
            if m is not None:
                dt = datetime.strptime(m.group('dt'), "%Y%m%dT%H%M")
                s3_trees_with_dt.append((dt, t))

        s3_trees_with_dt.sort(key=lambda x: x[0], reverse=True)
        return s3_trees_with_dt[0]

    def get_stored_info(self, target):
        self.connect()

        # If no local tree, load from S3
        print("Loading trees from S3")
        newest_tree = self.newest_s3_tree_key(target)
        tree_data = newest_tree.get_contents_as_string()
        old_tree = tree.load_tree(tree_data)

        return RemoteStoredInfo(tree_local_fname, all_trees)

    def save_tree(self, target, new_tree):
        self.connect()

        now_dt = datetime.utcnow()
        now_dt_str = now_dt.strftime('%Y%m%dT%H%M')
        sio = StringIO()
        tree.save_tree(new_tree, sio)

        # Save to S3
        print("Saving tree to S3")
        s3_pf_prefix = self.cp.get('options', 's3-pf-prefix')

        k = Key(self.s3_bucket)
        k.key = '{}/trees/{}.{}'.format(
                s3_pf_prefix,
                target,
                now_dt_str
                )
        k.set_metadata('pf:target', target)
        k.set_metadata('pf:saved_dt', now_dt_str)
        k.set_contents_from_string(sio.getvalue())

    def save_archive(self, filename):
        """Returns the archive ID of the saved object"""
        # Save to Glacier
        self.connect()

        gl_pf_prefix = self.cp.get('options', 'glacier-pf-prefix')
        basename = os.path.basename(filename)

        print("Saving archive {} to Glacier".format(basename))
        return self.gl_vault.create_archive_from_file(
                filename=filename,
                description="{} {}".format(gl_pf_prefix, basename)
                )

        # TODO: metadata in the description. filename, is_multi
        '''
        concurrent_create_archive_from_file doesn't seem to support descriptions yet
        return self.gl_vault.concurrent_create_archive_from_file(
                filename,
                "{} {}".format(gl_pf_prefix, basename)
                )
        '''
