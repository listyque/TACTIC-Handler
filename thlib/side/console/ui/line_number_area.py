from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore


class LineNumberArea(QtGui.QWidget):

    def __init__(self, editor=None):
        """
        Initialize default settings.
        """

        QtGui.QWidget.__init__(self, editor)
        self._editor = editor

    def sizeHint(self):
        """
        Get size hint.
        """

        return QtCore.QSize(self._editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        """
        Paint event.
        """

        self._editor.lineNumberAreaPaintEvent(event)