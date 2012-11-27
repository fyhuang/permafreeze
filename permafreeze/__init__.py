from __future__ import unicode_literals, print_function, absolute_import

import os
import sys
import time
import threading
import subprocess
import ConfigParser as configparser

import choice

#from permafreeze import config_interface

# From <http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python>
def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def open_url(url):
    open_fname = None
    if sys.platform.startswith('linux'):
        open_fname = which('gnome-open')
        if open_fname is None:
            open_fname = which('kde-open')
        if open_fname is None:
            open_fname = which('xdg-open')
        if open_fname is None:
            open_fname = which('links')
        #if open_fname is None:
        #    open_fname = which('lynx')
    elif sys.platform.startswith('darwin'):
        open_fname = 'open'
    elif sys.platform.startswith('win32'):
        open_fname = 'start'
    else:
        raise NotImplementedError('Your platform is not yet supported by permafreeze')

    if open_fname is None:
        print("Please open this webpage in your browser:\n{}".format(url))
    else:
        subprocess.call([open_fname, url])


def print_usage():
    print("Usage:\n\n\tfreeze command [args]")
    print("\nCommands:\n")
    for c in [('config', 'launch permafreeze configuration'),
            ]:
        print("{}:\t{}".format(c[0], c[1]))
    print()
    sys.exit(1)

def main(argv=None):
    if argv is None:
        argv = sys.argv

    if len(argv) < 2:
        print_usage()

    command = argv[1]
    if command == 'config':
        '''cit = threading.Thread(target=config_interface.start)
        cit.start()
        time.sleep(1)
        open_url('http://localhost:{}/'.format(config_interface.PORT))
        cit.join()'''
        newconfig = configparser.SafeConfigParser()
        newconfig.set(
    else:
        print("Unrecognized command {}".format(command))
        print_usage()

if __name__ == "__main__":
    sys.exit(main())
