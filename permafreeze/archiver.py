import os.path
import tarfile
import struct

import snappy

from permafreeze import storage

COMPRESS = 0
DECOMPRESS = 1

'''class SnappyStream(object):
    def __init__(self, target_file, mode=COMPRESS):
        self.fp = target_file
        self.mode = mode

        snappy_header = struct.pack('<BH', 0xff, 6)
        if mode == COMPRESS:
            # Write Snappy header
        else:
            # Check Snappy header

    def read(self, numbytes):
        assert self.mode == DECOMPRESS
        pass

    def write(self, data):
        assert self.mode == COMPRESS
        pass

    def flush(self):
        pass

    def close(self):
        self.flush()
'''

class Archiver(object):
    def __init__(self, cp, first_num, target_name, archive_size=50*1024*1024):
        self.cp = cp
        self.target_name = target_name

        self.curr_num = first_num-1
        self.archive_size = archive_size
        self.curr_archive = None
        self.curr_archive_size = 0

        self.num_to_id = {}

    def archive_name(self):
        return 'ar_{}_{}.tar'.format(
            self.target_name,
            self.curr_num
            )

    def local_archive_name(self):
        local_archive_dir = os.path.join(
            self.cp.get('options', 'config-dir'),
            'tmp'
            )
        return os.path.join(local_archive_dir, self.archive_name())

    def finish_archive(self):
        if self.curr_archive is not None:
            self.curr_archive.close()
            aid = storage.save_archive(self.cp, self.local_archive_name())
            self.num_to_id[self.curr_num] = aid
            os.unlink(self.local_archive_name())

        self.curr_num += 1

    def add_file(self, full_path, uukey, file_size):
        if self.curr_archive is None or \
                self.curr_archive_size >= self.archive_size:
            self.finish_archive()

            self.curr_archive = tarfile.open(
                    self.local_archive_name(),
                    mode='w'
                    )
            self.curr_archive_size = 0

        self.curr_archive.add(full_path, arcname=uukey)
        self.curr_archive_size += file_size

    def close(self):
        self.finish_archive()
