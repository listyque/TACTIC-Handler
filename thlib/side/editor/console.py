import os
import re
import sys
import uuid
import tempfile
from imp import new_module
from code import InteractiveConsole
from contextlib import contextmanager
from PySide2.QtCore import QThread, QMutex, Signal

try:
    from contextlib import redirect_stdout, redirect_stderr

except ImportError:
    @contextmanager
    def redirect_stdout(new_target):
        old_target, sys.stdout = sys.stdout, new_target
        try:
            yield new_target

        finally:
            sys.stdout = old_target


    @contextmanager
    def redirect_stderr(new_target):
        old_target, sys.stderr = sys.stderr, new_target
        try:
            yield new_target

        finally:
            sys.stderr = old_target


NEW_LINE_PAT = u"\n|\r|\r\n|\v|\x0b|\x0c|\x1c|\x1d|\x1e|\x1e|\x85|\u2028|\u2029"
NEW_LINE_EXP = re.compile(NEW_LINE_PAT)


class Console(QThread):
    finished = Signal()

    def __init__(self):
        super(Console, self).__init__()

        self._mutex = QMutex()

        self._console = InteractiveConsole()
        self._console.superspace = new_module("superspace")

        directory = os.path.join(tempfile.gettempdir(), 'code_editor')
        not os.path.isdir(directory) and os.makedirs(directory)
        self._output = os.path.join(directory, '{}.log'.format(str(uuid.uuid4()).replace('-', '_')))
        self._stdout = open(self._output, 'w', 1)
        self._source = None
        self.start()

    def output(self):
        return self._output

    def clear(self):
        self._stdout.close()
        self._stdout = open(self._output, 'w', 1)

    def enter(self, source):
        self._mutex.lock()
        self._source = source.lstrip(NEW_LINE_PAT)
        self._mutex.unlock()

    def run(self):
        while True:
            if self._source:
                self._mutex.lock()
                try:
                    # write input
                    func = self._console.runcode if NEW_LINE_EXP.search(self._source) else self._console.push
                    self._stdout.write(self._source)
                    self._stdout.write('\n')
                    self._stdout.flush()

                    with redirect_stdout(self._stdout), redirect_stderr(self._stdout):
                        text = func(self._source)
                        if text:
                            self._stdout.write(str(text))
                            self._stdout.write('\n')
                            self._stdout.flush()

                    self._stdout.flush()

                finally:
                    self._source = None
                    self._mutex.unlock()
                    self.finished.emit()

            else:
                self.sleep(1)
