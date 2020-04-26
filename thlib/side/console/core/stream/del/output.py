from thlib.side.Qt import QtCore


class Output(QtCore.QObject):

    written = QtCore.Signal(unicode)
    flushed = QtCore.Signal()

    def __init__(self, std, parent_stream=None, parent=None):

        """
        Initialize default settings.
        """

        self.__parent_stream = parent_stream

        super(Output, self).__init__(parent)

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
        
        result = self.__std.write(text)
        # try:
        #     # text = unicode(text).encode('utf-8', errors='ignore')
        #     text = str(text)
        #
        # except UnicodeEncodeError or UnicodeDecodeError:
        #     text = u"Failed to encode error message..."

        self.written.emit(text)
        return result

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
