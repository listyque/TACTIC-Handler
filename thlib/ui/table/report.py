"""Native paginated printing; TACTIC data never enters an HTML or web view."""

import base64

from PySide6.QtCore import QUrl
from PySide6.QtGui import (
    QImage,
    QTextCursor,
    QTextDocument,
    QTextImageFormat,
    QTextLength,
    QTextTableFormat,
)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import QDialog


def document(report: dict) -> QTextDocument:
    result = QTextDocument()
    cursor = QTextCursor(result)
    for index, block in enumerate(report['blocks']):
        if block['kind'] == 'image':
            image = QImage.fromData(base64.b64decode(block['data']))
            if image.isNull():
                raise ValueError('The report preview is not a readable image')
            name = QUrl('report:preview' + str(index))
            result.addResource(QTextDocument.ImageResource, name, image)
            image_format = QTextImageFormat()
            image_format.setName(name.toString())
            width = min(300, image.width())
            image_format.setWidth(width)
            image_format.setHeight(image.height() * width / image.width())
            cursor.insertImage(image_format)
        elif block['kind'] == 'table':
            cursor.insertText(block['title'])
            cursor.insertBlock()
            columns = block['columns']
            if columns:
                table_format = QTextTableFormat()
                table_format.setHeaderRowCount(1)
                table_format.setBorder(0.4)
                table_format.setCellPadding(4)
                table_format.setWidth(QTextLength(QTextLength.PercentageLength, 100))
                table = cursor.insertTable(
                    len(block['rows']) + 1, len(columns), table_format
                )
                for row, values in enumerate([columns, *block['rows']]):
                    for column, value in enumerate(values):
                        table.cellAt(row, column).firstCursorPosition().insertText(
                            value
                        )
                cursor = table.lastCursorPosition()
                cursor.movePosition(QTextCursor.NextBlock)
        else:
            cursor.insertText(block['text'])
        cursor.insertBlock()
    return result


def print_report(report: dict) -> None:
    printer = QPrinter(QPrinter.HighResolution)
    dialog = QPrintDialog(printer)
    if dialog.exec() == QDialog.Accepted:
        document(report).print_(printer)
