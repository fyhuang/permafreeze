from __future__ import division, absolute_import, print_function, unicode_literals

from collections import namedtuple

from permafreeze import formatpath


class StartedProcessingFile(namedtuple('StartedProcessingFile', ['target_path', 'full_path'])):
    def __repr__(self):
        return formatpath(self.target_path)

class ProcessFileResult(namedtuple('ProcessFileResult', ['result'])):
    def __repr__(self):
        return '\t... {}'.format(self.result)

class ProgressReport(namedtuple('ProgressReport', ['done', 'total'])):
    def __repr__(self):
        width = 50
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
