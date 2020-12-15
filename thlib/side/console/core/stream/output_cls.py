# -*- coding: utf-8 -*-
# encoding: utf-8

__all__ = ["OutputCls"]

import locale
from thlib.side.Qt import QtCore
from thlib.side import six


class OutputCls(QtCore.QObject):

    written = QtCore.Signal(object)

    encoding = locale.getpreferredencoding()

    def __init__(self, std, parent=None):

        """
        Initialize default settings.
        """

        super(OutputCls, self).__init__(parent)
        self.__std = std
        self.softspace = 0

    def readline(self, *args, **kwargs):
        
        """
        Read line method.
        """
        
        return self.__std.readline(*args, **kwargs)

    def write(self, text):

        """
        Write text message.
        """

        if text is not None:
            try:
                if six.PY2 and isinstance(text, (basestring, unicode)) or not six.PY2 and isinstance(text, str):
                    self.__std.write(text)
                else:
                    self.__std.write(repr(text))

                self.written.emit(text)
            except:
                pass

        return text

    def writelines(self, line_list):

        """
        Write lines.
        """

        result = self.__std.writelines(line_list)
        for line in line_list:
            try:
                line = six.PY2 and unicode(line) or six.u(line)

            except UnicodeEncodeError or UnicodeDecodeError:
                line = u"Failed to encode error message..."

            self.written.emit(line)

        return result

    def flush(self, *args, **kwargs):

        """
        Flush
        """
        result = self.__std.flush(*args, **kwargs)
        return result
