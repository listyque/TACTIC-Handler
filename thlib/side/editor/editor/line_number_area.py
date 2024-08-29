from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Qt, QSize, __version_info__ as QT_VERSION
from PySide2.QtGui import QPainter


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self._editor = editor

    def sizeHint(self):
        if self._editor is None:
            return super(LineNumberArea, self).sizeHint()

        digit = 1
        digit_max = max(1, self._editor.document().blockCount())
        while digit_max >= 10:
            digit_max /= 10
            digit += 1

        if QT_VERSION >= (5, 0, 0):
            space = 32 + self._editor.fontMetrics().horizontalAdvance('9') * digit

        else:
            space = 32 + self._editor.fontMetrics().width('9') * digit

        return QSize(space, 0)

    def paintEvent(self, event):
        if not self._editor:
            return None

        highligher = self._editor.highligher()
        style = highligher.style()
        painter = QPainter(self)

        # clearing rect to update
        painter.fillRect(
            event.rect(),
            style.getFormat("Text").background().color()
        )
    
        block = self._editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self._editor.blockBoundingGeometry(block).translated(self._editor.contentOffset()).top()
        bottom = top + self._editor.blockBoundingRect(block).height()
    
        current_line = style.getFormat("CurrentLineNumber").foreground().color()
        default_line = style.getFormat("LineNumber").foreground().color()

        painter.setFont(self._editor.font())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = block_number + 1

                is_current_line = self._editor.textCursor().blockNumber() == block_number
                painter.setPen(current_line if is_current_line else default_line)

                painter.drawText(
                    0,
                    int(top),
                    self.sizeHint().width(),
                    self._editor.fontMetrics().height(),
                    Qt.AlignLeft,
                    str(number)
                )

            block = block.next()
            top = bottom
            bottom = top + self._editor.document().documentLayout().blockBoundingRect(block).height()
            block_number += 1
