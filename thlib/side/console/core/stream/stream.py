# -*- coding: utf-8 -*-

__all__ = ["Stream"]

import sys
from thlib.side.Qt import QtCore


class Stream(QtCore.QObject):

    __stdout = None
    __stderr = None
    __excepthook = None
    __stream = None
    
    __original__stdout = sys.stdout
    __original__stdin = sys.stdin
    __original__stderr = sys.stderr
    __original__excepthook = sys.excepthook

    exceptedWritten = QtCore.Signal(unicode)
    outputWritten = QtCore.Signal(unicode)
    errorWritten = QtCore.Signal(unicode)
    inputWritten = QtCore.Signal(unicode)
    
    @staticmethod
    def get_stream():
        
        """
        Get current stream.
        """
        
        return Stream.__stream
    
    def __new__(cls, *args):
        
        """
        Get python stream instance.
        """
        
        if Stream.__stream is None:
            result = super(Stream, cls).__new__(cls, *args)
        else:
            result = Stream.__stream
        return result
    
    def __init__(self, *args):

        """
        Initialize default settings.
        """

        super(Stream, self).__init__(*args)
        
        if Stream.__stream is None:
            Stream.__stream = self
            from . import OutputCls, ExceptionHook

            self.out = OutputCls(Stream.__original__stdout, self)
            Stream.__stdout = self.out
            self.out.written.connect(self.writeOutput)

            self.inp = OutputCls(Stream.__original__stdin, self)
            Stream.__stdin = self.inp
            self.inp.written.connect(self.writeInput)

            self.err = OutputCls(Stream.__original__stderr, self)
            Stream.__stderr = self.err
            self.err.written.connect(self.writeError)

            self.excepthandler = ExceptionHook(Stream.__original__excepthook)
            Stream.__excepthook = self.excepthandler.excepthook

            sys.stdin = Stream.__stdin
            sys.stdout = Stream.__stdout
            sys.stderr = Stream.__stderr
            sys.excepthook = self.excepthandler.excepthook

            self.excepthandler.excepted.connect(self.writeExcepted)
            self.excepthandler.excepted.connect(self.writeErrorToStream)

            self.err_count = 0
            self.out_count = 0
            self.in_count = 0
        
    def writeErrorToStream(self, text):
        
        """
        Write string to error output.
        """
        
        # try:
        #     text = unicode(text)
        #
        # except UnicodeDecodeError or UnicodeEncodeError:
        #     text = u"Failed to encode error message..."

        Stream.__stderr.write(text)
        self.exceptedWritten.emit(text)
        
    def writeOutputToStream(self, text):
        
        """
        Write string to output.
        """
        
        # try:
        #     text = unicode(text)
        #
        # except UnicodeDecodeError or UnicodeEncodeError:
        #     text = u"Failed to encode error message..."

        Stream.__stdout.write(text)

    def writeInputToStream(self, text):
        
        """
        Write string to input output.
        """
        
        # try:
        #     text = unicode(text)
        #
        # except UnicodeDecodeError or UnicodeEncodeError:
        #     text = u"Failed to encode error message..."

        Stream.__stdin.write(text)
    
    def input(self, text):

        """
        Write input text.
        """

        # try:
        #     text = unicode(text)
        #
        # except UnicodeDecodeError or UnicodeEncodeError:
        #     text = u"Failed to encode error message..."

        self.writeInput(text)
        self.writeInput("\n")

    def writeInput(self, text):

        """
        Handle input text.
        """

        # try:
        #     text = unicode(text)
        #
        # except UnicodeDecodeError or UnicodeEncodeError:
        #     text = u"Failed to encode error message..."

        self.inputWritten.emit(text)
        
        if self.in_count < sys.maxint:
            self.in_count += 1

    def writeError(self, text):

        """
        Write error text.
        """

        # try:
        #     text = unicode(text)
        #
        # except UnicodeDecodeError or UnicodeEncodeError:
        #     text = u"Failed to encode error message..."

        self.errorWritten.emit(text)
        
        if self.err_count < sys.maxint:
            self.err_count += 1

    def writeOutput(self, text):

        """
        Write output text.
        """

        # try:
        #     text = unicode(text)
        #
        # except UnicodeDecodeError or UnicodeEncodeError:
        #     text = u"Failed to encode error message..."

        self.outputWritten.emit(text)
        
        if self.out_count < sys.maxint:
            self.out_count += 1
        
    def writeExcepted(self, text):
        
        """
        Write excepted.
        """
        
        # try:
        #     text = unicode(text)
        #
        # except UnicodeDecodeError or UnicodeEncodeError:
        #     text = u"Failed to encode error message..."

        self.exceptedWritten.emit(text)
        
        if self.err_count < sys.maxint:
            self.err_count += 1
