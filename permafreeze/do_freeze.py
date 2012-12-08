import os
import os.path
import stat
import datetime

def should_skip(cp, target_path, full_path, old_tree):
    if cp.getboolean('options', 'ignore-dotfiles'):
        if os.path.basename(full_path)[0] == '.':
            return True

    sb = os.stat(full_path)
    if not stat.S_ISREG(sb.st_mode) and \
            not stat.S_ISLNK(sb.st_mode):
        # Non-regular file or link
        return True

    mtime_dt = datetime.utcfromtimestamp(sb.st_mtime)
    try:
        old_entry = old_tree.files[target_path]
        # Make sure the data is stored
        if old_entry.uukey in old_tree.hashes:
            if old_entry.last_hashed >= mtime_dt:
                return True
    except KeyError: # old_tree.files doesn't contain target_path
        pass



    return False
