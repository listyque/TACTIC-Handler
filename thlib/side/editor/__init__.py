import os
from PySide2.QtWidgets import QWidget, QVBoxLayout, QSplitter, QPlainTextEdit
from PySide2.QtGui import QTextCursor
from PySide2.QtCore import Qt, QTimer
from .editor.base_editor import BaseEditor
from . import console


class CodeEditor(QWidget):
    def __init__(self, *args, **kwargs):
        super(CodeEditor, self).__init__(*args, **kwargs)
        self._layout = QVBoxLayout()
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        self._splitter = QSplitter()
        self._splitter.setStyleSheet("QSplitter::handle { background-color:palette(midlight) }")
        self._splitter.setOrientation(Qt.Vertical)
        self._layout.addWidget(self._splitter)

        self._editor = BaseEditor()
        # TODO: add tabs
        # self._editor.returnPressed.connect(self.run)
        self._splitter.addWidget(self._editor)

        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output_timer = QTimer()
        self._output_timer.timeout.connect(self.update)
        self._output_timer.setInterval(500)
        self._output_timer.start()
        self._output_seek = 0
        self._splitter.addWidget(self._output)

        self._console = console.Console()
        self._console.finished.connect(lambda: self._editor.setEnabled(True))

        self._editor_search_result = []
        self._editor.setPlainText(
'''
if (
        e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter
):
123456
123456
123456
123456
123456
'''
        )

    def clear(self):
        self._output_seek = 0
        self._output.clear()
        self._console.clear()

    def search(self, text, match_case=False, whole_word=False, regular=False, backward=False, wrap=False):
        self._editor_search_result = self._editor.search(
            text,
            match_case=match_case,
            whole_word=whole_word,
            regular=regular,
            backward=backward,
            wrap=wrap
        )

    def search_reset(self):
        self._editor.search_reset()

    def search_prev(self):
        self._editor.search_prev()

    def search_next(self):
        self._editor.search_next()

    def update(self):
        scroll_bar = self._output.verticalScrollBar()
        value = scroll_bar.value()
        scroll = value == scroll_bar.maximum()

        if os.path.exists(self._console.output()):
            with open(self._console.output(), 'r') as io:
                io.seek(self._output_seek)
                self._output.moveCursor(QTextCursor.End)
                self._output.textCursor().insertText(io.read())
                self._output.moveCursor(QTextCursor.End)
                self._output_seek = io.tell()

        if not scroll:
            scroll_bar.setValue(value)

        else:
            scrollbar = self._output.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            self._output.moveCursor(QTextCursor.End)

    def run(self, all=False):
        self._editor.setEnabled(False)

        text = ''
        if all is False:
            text = self._editor.selected_text()

        if not text or text == '':
            text = self._editor.toPlainText()

        text = text.replace(u"\u2029", "\n").replace(u"\u2028", "\n")

        scrollbar = self._output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self._output.moveCursor(QTextCursor.End)

        self._console.enter(text)
