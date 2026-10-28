"""Formatting a reader must settle instead of feeding its text-change handler."""

from types import SimpleNamespace
import unittest

from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QTextDocument, QTextTable
from PySide6.QtTest import QSignalSpy, QTest

from tests import test_frame_table as frames
from tests.test_columns_table_view import _TableColumns, _TableController
from tests.test_custom_layout import Services
from thlib.ui.rich_text_document import format_readonly_document


TEXT = '\n\n'.join(f'## Section {index}\nA report with **formatted** text.'
                   for index in range(35)) + '\n\n```python\nprint(1)\nprint(2)\n```\n\n| A | B |\n|---|---|\n| One | Two |'
STYLE = dict(paragraphGap=8, headingGap=14, lineHeight=17,
             headingLineHeight=22.5, cellPadding=4, borderColor='#555555')


class ReaderServices(Services):
    calls = 0

    @Slot(QObject, 'QVariantMap')
    def format_document(self, document, style):
        self.calls += 1
        format_readonly_document(document, style)


class ReadonlyDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item

    def test_same_paragraph_and_table_style_does_not_change_document(self):
        document = QTextDocument()
        document.setMarkdown(TEXT)
        wrapper = SimpleNamespace(textDocument=lambda: document)
        text = document.toPlainText()
        format_readonly_document(wrapper, STYLE)
        changes = QSignalSpy(document.contentsChanged)
        for _ in range(3):
            format_readonly_document(wrapper, STYLE)
        self.assertEqual(changes.count(), 0)
        self.assertEqual(document.toPlainText(), text)
        self.assertEqual(document.begin().blockFormat().topMargin(), 14)
        table = next(child for child in document.rootFrame().childFrames()
                     if isinstance(child, QTextTable))
        self.assertEqual(table.format().cellPadding(), 4)
        updated = dict(STYLE, paragraphGap=10, cellPadding=6)
        format_readonly_document(wrapper, updated)
        self.assertGreater(changes.count(), 0)
        self.assertEqual(table.format().cellPadding(), 6)
        count = changes.count()
        format_readonly_document(wrapper, updated)
        self.assertEqual(changes.count(), count)

    def test_real_report_reader_stops_formatting_when_idle(self):
        services = ReaderServices(dict(layoutView='dashboard.idle', layoutNodes=[
            dict(kind='markdown', text=TEXT)]))
        window, view = self.create('features/table/CustomLayoutView.qml', dict(
            services=services, controller=_TableController(),
            columnsController=_TableColumns(), users=None, administration=None),
            width=1000, height=700)
        frames.frame(window)
        count = services.calls
        self.assertGreater(count, 0)
        self.assertLessEqual(count, 2)
        QTest.qWait(100)
        self.assertEqual(services.calls, count)
        body = self.item(view, 'documentBody')
        self.assertIn('Section 34', body.property('text'))
        services.state['layoutNodes'][0]['text'] = '# Updated report\n\nNew content'
        services.documentChanged.emit()
        frames.frame(window)
        self.assertIn('Updated report', body.property('text'))
        self.assertGreater(services.calls, count)
        count = services.calls
        QTest.qWait(100)
        self.assertEqual(services.calls, count)


if __name__ == '__main__':
    unittest.main()
