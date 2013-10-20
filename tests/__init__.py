from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future import standard_library
from future.builtins import *

import os
import os.path
import struct
import random

from permafreeze import PfConfig

TESTS_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_FILES_DIR = os.path.join(TESTS_MODULE_DIR, "files")
TEST_FILES_TGT = "testfiles"

def get_test_config():
    cp = PfConfig()
    cp.add_section("options")
    cp.set("options", "site-name", "testsite")
    cp.set("options", "s3-bucket-name", "testsite")
    cp.set("options", "glacier-vault-name", "testsite")
    cp.set("options", "s3-create-bucket", "True")
    cp.set("options", "config-dir", "cfg")
    cp.add_section("targets")
    cp.set("targets", TEST_FILES_TGT, TEST_FILES_DIR)

    cp.set("options", "s3-host", "127.0.0.1")
    cp.set("options", "s3-port", "4567")

    cp.add_section("auth")
    cp.set("auth", "accessKeyId", "AKID")
    cp.set("auth", "secretAccessKey", "SAK")

    cp.set_default_options()
    return cp

def gen_test_files(conf):
    files_path = conf.tempdir('files', create=False)
    if os.path.isdir(files_path):
        return

    # Generate the files
    int_s = struct.Struct('@I')
    kb_random = ''.join([int_s.pack(random.getrandbits(32)) for i in 256])
    os.mkdir(files_path)
    for size_kb in [16, 64, 1024, 16*1024, 20*1024]:
        # Make a file of size `size_kb`
        with open('file_{}k.dat'.format(size_kb), 'wb') as f:
            for i in range(size_kb):
                f.write(kb_random)
