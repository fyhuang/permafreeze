import os.path
import tarfile
import struct

import snappy

from permafreeze.storage import AmazonStorage

COMPRESS = 0
DECOMPRESS = 1

def archive_name(cp, target_name, arnum):
    return 'ar_{}_{}.tar'.format(
        target_name,
        arnum
        )

def local_archive_dir(cp):
    local_archive_dir = os.path.join(
        cp.get('options', 'config-dir'),
        'tmp'
        )
    return local_archive_dir

class Archiver(object):
    def __init__(self, cp, first_num, target_name, extstorage, archive_size=50*1024*1024):
        self.cp = cp
        self.target_name = target_name

        self.curr_num = first_num
        self.archive_size = archive_size
        self.curr_archive = None
        self.curr_archive_size = 0

        self.num_to_id = {}
        self.extstorage = extstorage

    def curr_archive_name(self):
        return archive_name(self.cp, self.target_name, self.curr_num)

    def curr_archive_path(self):
        return os.path.join(
                local_archive_dir(self.cp),
                self.curr_archive_name(),
                )

    def finish_archive(self):
        if self.curr_archive is not None:
            self.curr_archive.close()

            aid = self.extstorage.save_archive(self.curr_archive_path())
            self.num_to_id[self.curr_num] = aid
            os.unlink(self.curr_archive_path())
            self.curr_archive = None

        self.curr_archive_size = 0

    def add_file(self, full_path, uukey, file_size):
        if self.curr_archive is None or \
                self.curr_archive_size >= self.archive_size:

            print("Starting archive {}".format(self.curr_archive_name()))
            self.finish_archive()
            self.curr_num += 1
            self.curr_archive = tarfile.open(
                    self.curr_archive_path(),
                    mode='w'
                    )

        self.curr_archive.add(full_path, arcname=uukey)
        self.curr_archive_size += file_size

    def close(self):
        self.finish_archive()
