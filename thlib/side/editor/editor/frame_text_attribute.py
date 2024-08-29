from PySide2.QtGui import QPainter, QFontMetrics, QTextFormat, QTextCharFormat, QTextObjectInterface
from PySide2.QtCore import QRectF, QObject, QSize


class FrameTextAttribute(QObject, QTextObjectInterface):
    FormatType = 2

    def __init__(self, editor=None):
        super(FrameTextAttribute, self).__init__(editor)
        self._editor = editor

    def prop(self):
        return QTextFormat.UserProperty + FrameTextAttribute.FormatType

    def type(self):
        return QTextFormat.UserFormat + FrameTextAttribute.FormatType

    def language(self):
        return self._editor.language()

    def intrinsicSize(self, document, line, fmt):
        return QSize(0, 0)

    def drawObject(self, painter, rect, document, line, fmt):
        # casting
        text_fmt = QTextCharFormat(fmt)

        # getting font data
        font = text_fmt.font()
        metrics = QFontMetrics(font)

        # getting required size
        string = str(fmt.property(self.prop()))
        string_size = metrics.boundingRect(string).size()

        # creating frame rect
        draw_rect = QRectF(rect.topLeft(), string_size)
        draw_rect.moveTop(rect.top() - string_size.height())
        draw_rect.adjust(0, 4, 0, 4)

        # drawing
        painter.setPen(self.language().style().getFormat("Occurrences").background().color())
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawRoundedRect(draw_rect, 4, 4)

    def frame(self, cursor):
        text_fmt = QTextCharFormat()
        text_fmt.setObjectType(self.type())
        text_fmt.setProperty(self.prop(), cursor.selectedText())

        if cursor.selectionEnd() > cursor.selectionStart():
            cursor.setPosition(cursor.selectionStart())

        else:
            cursor.setPosition(cursor.selectionEnd())

        cursor.insertText(str(0xfffc), text_fmt)

    def unframe(self, cursor):
        text_fmt = cursor.charFormat()
        if text_fmt.type() == self.type():
            cursor.deleteChar()
            return True

        return False

    def clear(self, cursor):
        doc = cursor.document()

        for blockIndex in range(doc.blockCount()):
            block = doc.findBlockByNumber(blockIndex)

            formats = block.textFormats()
            offset = 0

            for fmt in formats:
                if fmt.format.objectType() == self.type():
                    cursor.setPosition(block.position() + fmt.start - offset)
                    cursor.deleteChar()
                    offset += 1
