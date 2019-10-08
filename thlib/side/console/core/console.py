import re
from imp import new_module
from code import InteractiveConsole


class Console(InteractiveConsole):

    kNewLine = u"\n|\r|\r\n|\v|\x0b|\x0c|\x1c|\x1d|\x1e|\x1e|\x85|\u2028|\u2029"
    kNewLineExpr = re.compile(kNewLine)

    def __init__(self, names=None):

        """
        initialize default settings.
        """

        names = names or {}
        names["console"] = self
        InteractiveConsole.__init__(self, names)
        self.superspace = new_module("superspace")

    def enter(self, source):

        """
        Send script.
        """

        source = source.lstrip(Console.kNewLine)
        if Console.kNewLineExpr.search(source):
            result = self.runcode(source)

        else:
            result = self.push(source)

        return result
