# -*- coding: utf-8 -*-

__all__ = ["ExceptionHook"]

import exceptions
import traceback
import types
import sys

from thlib.side.Qt import QtCore


class ExceptionHook(QtCore.QObject):
    
    excepted = QtCore.Signal(unicode)
    instance = None
    
    def __init__(self, excepthook, parent=None):

        super(ExceptionHook, self).__init__(parent)

        ExceptionHook.instance = self
        self.__excepthook = excepthook  # Backup original excepthook object.
        
    @staticmethod
    def __get_excepthook(*args):

        return ExceptionHook.get_traceback()
        
    def excepthook(self, *args):

        result = ExceptionHook.__get_excepthook(*args)
        self.excepted.emit(result)
        
    @staticmethod
    def request():

        exc_type, exc_value, exc_traceback = sys.exc_info()
        result = ExceptionHook.__get_excepthook(exc_type, exc_value, exc_traceback)
        if ExceptionHook.instance:
            ExceptionHook.instance.excepted.emit(result)

    @staticmethod
    def get_traceback():

        result = u""

        # Get information about latest traceback.
        exception_type, exception_value, exception_traceback = sys.exc_info()

        # Get exception as string.
        exception_type_string = exception_type is not None and exception_type.__name__ or u"UnknownError"
        exception_value_string = exception_value is not None and exception_value.message or u"Unknown error handled"

        # Get formatted traceback data.
        if hasattr(traceback, "format_exception"):
            format_traceback = traceback.format_exception(exception_type, exception_value, exception_traceback, limit=100)

        else:
            format_traceback = None

        if format_traceback:
            # Create traceback data list.
            if isinstance(format_traceback, (list, set, tuple)):
                format_traceback_list = list(format_traceback)

            else:
                format_traceback_list = [format_traceback]

            # Create traceback string.
            for format_traceback in format_traceback_list:
                try_unicode = True
                if isinstance(format_traceback, (basestring, unicode)):
                    try:
                        result += format_traceback

                    except Exception as exception_data:
                        try_unicode = True

                else:
                    try:
                        result += format_traceback.__repr__()

                    except Exception as exception_data:
                        try_unicode = True

                if try_unicode:
                    try:
                        result += unicode(format_traceback)

                    except Exception as exception_data:
                        result += u"(Can`t decode Exception data)"

        # Get default traceback string.
        if not result:
            result = u"Error: " + exception_value_string + u"\n" + exception_type_string + u": " + exception_value_string

        # Return traceback string.
        return result
