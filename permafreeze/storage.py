from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import collections
from StringIO import StringIO
from datetime import datetime

from boto.s3.connection import S3Connection, Key
from boto.glacier import layer2, vault

from permafreeze import tree

RemoteStoredInfo = collections.namedtuple('RemoteStoredInfo',
        ['tree_local_fname', 'last_tree'])
AmazonConns = collections.namedtuple('AmazonConns',
        ['s3_conn', 's3_bucket', 'gl_conn', 'gl_vault'])

_conns = None
def connect(cp):
    global _conns
    if _conns is None:
        s3_conn = S3Connection(cp.get('auth', 'accessKeyId'),
                        cp.get('auth', 'secretAccessKey'))
        s3_bucket = s3_conn.get_bucket(cp.get('options', 's3-bucket-name'))

        gl_conn = layer2.Layer2(
                aws_access_key_id=cp.get('auth', 'accessKeyId'),
                aws_secret_access_key=cp.get('auth', 'secretAccessKey')
                )
        gl_vault = gl_conn.create_vault(cp.get('options', 'glacier-vault-name'))

        _conns = AmazonConns(s3_conn, s3_bucket, gl_conn, gl_vault)
        

def get_stored_info(cp, target):
    connect(cp)

    s3_pf_prefix = cp.get('options', 's3-pf-prefix')


    # Try local tree
    tree_local_fname = os.path.join(cp.get('options', 'config-dir'), 'tree-'+target)
    if os.path.isfile(tree_local_fname):
        with open(tree_local_fname, 'rb') as f:
            old_tree = tree.load_tree(f.read())
    else:
        old_tree = tree.Tree()

    # If no local tree, load from S3
    print("Loading trees from S3")
    all_s3_trees = _conns.s3_bucket.list(s3_pf_prefix + '/trees/')
    for t in all_s3_trees:
        print(t)


    return RemoteStoredInfo(tree_local_fname, old_tree)

def save_tree(cp, target, new_tree):
    connect(cp)

    now_dt = datetime.utcnow()
    sio = StringIO()
    tree.save_tree(new_tree, sio)

    tree_local_fname = os.path.join(cp.get('options', 'config-dir'), 'tree-'+target)
    with open(tree_local_fname, 'wb') as f:
        f.write(sio.getvalue())

    # Save to S3
    print("Saving tree to S3")
    s3_pf_prefix = cp.get('options', 's3-pf-prefix')

    k = Key(_conns.s3_bucket)
    k.key = '{}/trees/{}.{}'.format(
            s3_pf_prefix,
            target,
            now_dt.strftime('%Y%m%dT%H%M')
            )
    k.set_contents_from_string(sio.getvalue())

def save_archive(cp, filename):
    # Save to Glacier
    connect(cp)

    gl_pf_prefix = cp.get('options', 'glacier-pf-prefix')
    basename = os.path.basename(filename)

    print("Saving archive {} to Glacier".format(basename))
    return _conns.gl_vault.create_archive_from_file(
            filename=filename,
            description="{} {}".format(gl_pf_prefix, basename)
            )
    '''
    concurrent_create_archive_from_file doesn't seem to support descriptions yet
    return _conns.gl_vault.concurrent_create_archive_from_file(
            filename,
            "{} {}".format(gl_pf_prefix, basename)
            )
    '''
