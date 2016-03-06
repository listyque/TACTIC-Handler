#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import fnmatch
import sys
import time
import optparse
from distutils.sysconfig import get_python_lib


class UiConverter(object):
    """ Uses platform and toolkit depended tools to convert *.ui and *.qrc files
    to Python
    """
    def __init__(self, qt_toolkit='pyside'):
        """
        :param qt_toolkit: Toolkit used to generate files: ``'pyside'`` or ``'pyqt'``
        """
        if qt_toolkit.lower() == 'pyside':
            if sys.platform.startswith('win'):
                PYPATH =  os.path.dirname(sys.executable)
                PYSIDEPATH = os.path.join(get_python_lib(), 'PySide')
                self.PYUIC = os.path.join(PYPATH, "Scripts/pyside-uic")
                self.PYRCC = os.path.join(PYSIDEPATH, "pyside-rcc")
            else:
                self.PYUIC = "pyside-uic"
                self.PYRCC = "pyside-rcc"
        else:  # pyqt
            if sys.platform.startswith('win'):
                PYQTPATH = os.path.join(get_python_lib(), 'PyQt4')
                self.PYUIC = os.path.join(PYQTPATH, "pyuic4")
                self.PYRCC = os.path.join(PYQTPATH, "pyrcc4.exe")
            else:
                self.PYUIC = "pyuic4"
                self.PYRCC = "pyrcc4"

    def convert_all_files_in_path(self, path):
        if not os.path.exists(path):
            print("'%s': Path doesn't exists. Skipping" % path)
            return
        count = 0
        for filename in os.listdir(path):
            full_path = os.path.join(path, filename)
            only_name, ext = os.path.splitext(full_path)
            cmd = None
            pyfile = None
            if fnmatch.fnmatch(filename, '*.ui'):
                pyfile = '%s.py' % only_name
                cmd = self.PYUIC
            elif fnmatch.fnmatch(filename, '*.qrc'):
                pyfile = '%s_rc.py' % only_name
                cmd = self.PYRCC
            if cmd and modified(full_path, pyfile):
                cmd_string = '%s -o "%s" "%s"' % (cmd, pyfile, full_path)
                os.system(cmd_string)
                count += 1
        print("'%s': %s converted %s files" % (path, time.ctime(time.time()), count))


def modified(source, dest):
    if not os.path.isfile(dest):
        return True
    delta = (os.path.getmtime(dest) - os.path.getmtime(source))
    return delta < 1


def main(qt_toolkit='pyside'):
    parser = optparse.OptionParser(usage='%prog [options] [paths]')
    parser.add_option('-w', '--watch', dest='watch',
                      action='store_true', default=False,
                      help='Watch files for change')
    parser.add_option('-i', '--interval', dest='interval', metavar='SECONDS',
                      action='store', type='float', default=3.0,
                      help='Directory scan interval, default %default seconds')
    options, args = parser.parse_args()

    if not args:
        args.extend(['./', 'ui'])
    if options.watch:
        print('Watching for file changes.\nPress CTRL+C to exit...')
    converter = UiConverter(qt_toolkit)
    try:
        while True:
            for path in args:
                converter.convert_all_files_in_path(path)
            if not options.watch:
                break
            time.sleep(options.interval)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()