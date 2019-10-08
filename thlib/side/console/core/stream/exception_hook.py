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

        exception_type, exception_value, exception_traceback = None, None, None
        for arg in args:
            if isinstance(arg, type):
                exception_type = arg

            elif isinstance(arg, exceptions.BaseException):
                exception_value = arg

            elif isinstance(arg, types.TracebackType):
                exception_traceback = arg
        
        exception_type_string = exception_type is not None and exception_type.__name__ or "UnknownError"
        exception_value_string = exception_value is not None and exception_value.message or "Unknown error handled"
        
        result = ""
        if exception_type is not None and exception_value is not None and exception_traceback is not None:
            python_traceback = Traceback.get_traceback(exception_traceback)
            result_temp = traceback.format_exception(exception_type, exception_value, python_traceback, limit=10)
            result = ""
            if result_temp:
                if isinstance(result_temp, (list, set, tuple)):
                    result_temp = list(result_temp)

                else:
                    result_temp = [result_temp]

                for result_temp_item in result_temp:
                    if isinstance(result_temp_item, (basestring, unicode)):
                        result += result_temp_item

                    else:
                        try:
                            result += result_temp_item.__repr__()

                        except UnicodeDecodeError or UnicodeEncodeError:
                            try:
                                result += str(result_temp_item)

                            except UnicodeDecodeError or UnicodeEncodeError:
                                result += "(Failed to decode Exception data)"
                    result += "\n"
        if not result:
            result = "Error: " + exception_value_string + "\n" + exception_type_string + ": " + exception_value_string

        return result
        
    def excepthook(self, *args):

        result = ExceptionHook.__get_excepthook(*args)
        self.excepted.emit(result)
        
    @staticmethod
    def request():

        exc_type, exc_value, exc_traceback = sys.exc_info()
        result = ExceptionHook.__get_excepthook(exc_type, exc_value, exc_traceback)
        if ExceptionHook.instance:
            ExceptionHook.instance.excepted.emit(result)


class Traceback(object):
    
    @staticmethod
    def get_traceback(tb_obj):

        result = Traceback(tb_obj.tb_frame, tb_obj.tb_lineno, tb_obj.tb_next)
        return result
    
    def __init__(self, tb_frame, tb_lineno, tb_next):

        self.tb_frame = tb_frame
        self.tb_lineno = tb_lineno
        self.tb_next = tb_next
            
    def stack(self):

        stack = []
        frame = self.tb_frame
        while frame is not None:
            stack.append((frame, frame.f_lineno))
            frame = frame.f_back

        return stack
        
    def extend(self):

        stack = self.stack()
        head = self
        for tb_frame, tb_lineno in stack:
            head = Traceback(tb_frame, tb_lineno, head)

        return head
