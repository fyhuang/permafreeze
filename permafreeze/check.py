from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
from datetime import datetime

from permafreeze import files_to_consider, uukey_and_size
from permafreeze.logger import log
from permafreeze.messages import ProgressReport

def do_check(conf, old_tree, target_name):
    errors = []
    done_files = 0
    skipped_files = 0
    total_files = sum(1 for i in files_to_consider(conf, target_name))

    for (full_path, target_path) in files_to_consider(conf, target_name):
        if os.path.islink(full_path):
            # TODO
            skipped_files += 1
            continue

        done_files += 1
        if done_files % 100 == 0:
            log(ProgressReport(done_files, total_files))

        mtime_dt = datetime.utcfromtimestamp(os.path.getmtime(full_path))
        check = True
        try:
            old_entry = old_tree.files[target_path]
            if old_entry.last_hashed < mtime_dt:
                # File has been modified, can't check consistency
                check = False
        except KeyError:
            check = False

        if not check:
            skipped_files += 1
            continue

        uukey, file_size = uukey_and_size(full_path)
        if uukey != old_entry.uuid:
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


