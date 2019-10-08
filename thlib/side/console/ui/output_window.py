from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore


class OutputWindow(QtGui.QPlainTextEdit):

    def __init__(self, parent=None):

        """
        Initialize default settings.
        """

        QtGui.QPlainTextEdit.__init__(self, parent)

        self.setTabStopWidth(4 * self.fontMetrics().width(" "))

        self.__current_write_state = "output"

    def scroll_to_bottom(self):

        """
        Scroll to bottom.
        """

        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.moveCursor(Qt4Gui.QTextCursor.End)

    def write_input(self, text):

        if self.__current_write_state != "input":
            self.__current_write_state = "input"

        # text = unicode(text)
        text = text.replace("\\r", "\r")
        text = text.replace("\\n", "\n")
        text = text.replace(" ", "&nbsp;")
        for line in text.splitlines():
            line = '<font color="#A9A9A9">' + line + '</font><br>'
            self.__write_html_output(line)
            # QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)

        self.scroll_to_bottom()

    def write_output(self, text):

        if self.__current_write_state != "output":
            self.__current_write_state = "output"

        # text = unicode(text)
        text = text.replace("\\r", "\r")
        text = text.replace("\\n", "\n")
        self.moveCursor(Qt4Gui.QTextCursor.End)
        self.insertPlainText(text)
        self.moveCursor(Qt4Gui.QTextCursor.End)
        # QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)
        self.scroll_to_bottom()

    def write_error(self, text):

        if self.__current_write_state != "error":
            self.__current_write_state = "error"

        # text = unicode(text)
        text = text.replace("\\r", "\r")
        text = text.replace("\\n", "\n")
        text = text.replace(" ", "&nbsp;")
        for line in text.splitlines():
            line = '<font color="#ff9999">' + line + '</font><br>'
            self.__write_html_output(line)
            # QtGui.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)

        self.scroll_to_bottom()

    def __write_html_output(self, text):

        """
        Write text as html output.
        """

        self.moveCursor(Qt4Gui.QTextCursor.End)
        self.textCursor().insertHtml(text)
        self.moveCursor(Qt4Gui.QTextCursor.End)
