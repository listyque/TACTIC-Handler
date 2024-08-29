from PySide2.QtGui import QPainter, QFontMetrics, QTextFormat, QTextCharFormat, QTextObjectInterface, QTextDocumentFragment
from PySide2.QtCore import QRectF, QObject


class FoldTextAttribute(QObject, QTextObjectInterface):
    FormatType = 3

    def __init__(self, editor=None):
        super(FoldTextAttribute, self).__init__(editor)
        self._editor = editor

    def prop(self):
        return QTextFormat.UserProperty + FoldTextAttribute.FormatType

    def type(self):
        return QTextFormat.UserFormat + FoldTextAttribute.FormatType

    def language(self):
        return self._editor.language()

    def intrinsicSize(self, document, line, fmt):
        text_fmt = QTextCharFormat(fmt)
        font = text_fmt.font()
        metrics = QFontMetrics(font)

        size = metrics.boundingRect('...').size()
        return size

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
        painter.drawText(draw_rect, '...')

    def fold(self, cursor):
        text_fmt = QTextCharFormat()
        text_fmt.setObjectType(self.type())
        text_fmt.setProperty(self.prop(), cursor.selection())
        cursor.insertText(str(0xfffc), text_fmt)

    def unfold(self, cursor):
        if not cursor.hasSelection():
            text_fmt = cursor.charFormat()
            if text_fmt.objectType() == self.type():
                cursor.movePosition(cursor.Left, cursor.KeepAnchor)
                value = text_fmt.property(self.prop())
                fragment = QTextDocumentFragment(value)
                cursor.insertFragment(fragment)
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
