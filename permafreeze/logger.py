from __future__ import division, absolute_import, print_function, unicode_literals

from multiprocessing import Queue

def printmsg(obj):
    print(obj)

callback = printmsg
channel = Queue()

def log(obj):
    channel.put(obj)
    if callback is not None:
        callback(obj) 

def set_cb(cb):
    global callback
    callback = cb

def reset_cb():
    global callback
    callback = printmsg
