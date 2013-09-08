from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import uuid
import tarfile
import struct
from StringIO import StringIO
from contextlib import closing

import snappy

from permafreeze.storage import AmazonStorage

COMPRESS = 0
DECOMPRESS = 1

# TODO: rename Archiver to Packer
class Archiver(object):
    def __init__(self, conf, target_name, archive_size=50*1024*1024):
        self.cp = conf
        self.archive_dir = self.cp.tempdir('archives')
        self.target_name = target_name

        self.curr_uuid = None
        self.archive_size = archive_size
        self.curr_archive = None
        self.curr_archive_size = 0

        self.cb = None

    def set_callback(self, cb):
        self.cb = cb

    def _curr_archive_filepath(self):
        return os.path.join(
                self.archive_dir,
                'ar_{}_{}.tar'.format(self.target_name, self.curr_uuid)
                )

    def finish_archive(self):
        if self.curr_archive is not None:
            self.curr_archive.close()

            self.cb(self.curr_uuid, self._curr_archive_filepath())
            self.curr_archive = None

        self.curr_archive_size = 0

    def add_archive_info(self):
        arinfo_file = StringIO(self.curr_uuid)
        with closing(arinfo_file) as arinfo_file:
            arinfo_ti = tarfile.TarInfo(".ARCHIVE_INFO_PF")
            arinfo_ti.size = len(arinfo_file.getvalue())
            arinfo_ti.type = tarfile.REGTYPE
            # TODO: add other metadata (in JSON format?)
            self.curr_archive.addfile(arinfo_ti, arinfo_file)

    def add_file(self, full_path, uukey, file_size):
        if self.cb is None:
            raise NotImplementedError

        # Make sure that file_size is accurate
        assert file_size == os.path.getsize(full_path)

        if self.curr_archive is None or \
                self.curr_archive_size >= self.archive_size:

            self.finish_archive()
            self.curr_uuid = 'P' + uuid.uuid4().hex[15:]
            self.curr_archive = tarfile.open(
                    self._curr_archive_filepath(),
                    mode='w'
                    )
            self.add_archive_info()

            print("Starting archive {}".format(self.curr_uuid))

        self.curr_archive.add(full_path, arcname=uukey)
        self.curr_archive_size += file_size
        return self.curr_uuid

    def close(self):
        # TODO: with statement
        self.finish_archive()
