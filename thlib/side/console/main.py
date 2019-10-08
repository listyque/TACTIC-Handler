import sys
from PySide import QtCore, QtGui
from core import console, stream
from ui import editor_window, output_window


class Window(QtGui.QWidget):

    def __init__(self, *args, **kwargs):

        super(Window, self).__init__(*args, **kwargs)
        self.__layout = QtGui.QVBoxLayout()
        self.__layout.setSpacing(0)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__layout)

        self.splitter = QtGui.QSplitter()
        self.splitter.setStyleSheet("QSplitter::handle { background-color:palette(midlight) }")
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.__layout.addWidget(self.splitter)

        self.output = output_window.OutputWindow(self)
        self.splitter.addWidget(self.output)

        self.stream = stream.Stream.get_stream()
        if self.stream is None:
            self.stream = stream.Stream()

        self.stream.outputWritten.connect(self.output.write_output)
        self.stream.errorWritten.connect(self.output.write_error)
        self.stream.inputWritten.connect(self.output.write_input)

        self.console = editor_window.EditorWindow(self)
        self.console.returnPressed.connect(self.run)
        self.splitter.addWidget(self.console)

        self.console_obj = console.Console()

    def runall(self):

        self.run(all=True)

    def run(self, all=False):

        if all is False:
            text = self.console.selectedText()

        else:
            text = self.console.toPlainText()

        text = text.replace(u"\u2029", "\n")
        text = text.replace(u"\u2028", "\n")
        if not text or text == "":
            text = self.console.toPlainText()

        self.output.moveCursor(QtGui.QTextCursor.End)
        self.stream.input(text)

        self.output.scroll_to_bottom()
        self.console_obj.enter(text)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainWin = Window()
    mainWin.show()
    sys.exit(app.exec_())
