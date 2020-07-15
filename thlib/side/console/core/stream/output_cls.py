# -*- coding: utf-8 -*-
# encoding: utf-8

__all__ = ["OutputCls"]

import locale
from thlib.side.Qt import QtCore


class OutputCls(QtCore.QObject):

    written = QtCore.Signal(object)
    flushed = QtCore.Signal()

    encoding = locale.getpreferredencoding()

    def __init__(self, std, parent_stream=None, parent=None):

        """
        Initialize default settings.
        """
        # self.__io = open('D:/APS/OneDrive/MEGAsync/TACTIC-handler/stuff.txt', 'w')
        self.__parent_stream = parent_stream

        super(OutputCls, self).__init__(parent)

        self.__std = std
        self.softspace = 0

    def readline(self, *args, **kwargs):
        
        """
        Read line method.
        """
        
        return self.__std.readline(*args, **kwargs)
        
    def stream(self):
        
        """
        Get parent stream.
        """
        
        return self.__parent_stream
    
    def write(self, text):

        """
        Write text message.
        """

        # if text is not None:
        #     if isinstance(text, (str, unicode)):
        #         self.__std.write(text)
        #     else:
        #         self.__std.write(repr(text))

        try:
            self.__std.write(text)
            self.written.emit(text)
        except:
            pass
        finally:
            return text

        # try:
        #     # text = unicode(text).encode('utf-8', errors='ignore')
        #     text = str(text)
        #
        # except UnicodeEncodeError or UnicodeDecodeError:
        #     text = u"Failed to encode error message..."

        # self.written.emit(text)
        # return result

    def writelines(self, line_list):

        """
        Write lines.
        """

        result = self.__std.writelines(line_list)
        for line in line_list:
            # try:
            #     line = unicode(line)
            #
            # except UnicodeEncodeError or UnicodeDecodeError:
            #     line = u"Failed to encode error message..."

            self.written.emit(line)

        return result

    def flush(self, *args, **kwargs):

        """
        Flush
        """
        result = self.__std.flush(*args, **kwargs)
        self.flushed.emit()
        return result
