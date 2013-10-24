from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future import standard_library
from future.builtins import *

from io import StringIO
from collections import namedtuple

from permafreeze import formatpath


class StartedProcessingFile(namedtuple('StartedProcessingFile', ['target_path', 'full_path'])):
    def __repr__(self):
        return formatpath(self.target_path)

class ProcessFileResult(object):
    def __init__(self, result, reason=None, uuid=None):
        self.result = result
        self.uuid = uuid
        self.reason = reason

    def __repr__(self):
        if self.result == 'Skip':
            return '\t... {} ({})'.format(self.result, self.reason)
        else:
            return '\t... {}'.format(self.result)

class ProgressReport(namedtuple('ProgressReport', ['done', 'total'])):
    def __repr__(self):
        width = 50
        if self.total == 0:
            ratio = 1.0
        else:
            ratio = self.done / self.total

        sio = StringIO()
        sio.write('[')
        for i in range(width):
            cratio = i / width
            if cratio <= ratio:
                sio.write('#')
            else:
                sio.write(' ')
        sio.write("] {}%".format(ratio * 100))
        return sio.getvalue()

class PackStarted(namedtuple('PackStarted', ['pack_uuid'])):
    def __repr__(self):
        return 'Starting pack {}'.format(self.pack_uuid)
