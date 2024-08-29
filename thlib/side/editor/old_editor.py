import os
import json
from PySide2.QtWidgets import QWidget, QPlainTextEdit, QTextEdit, QApplication
from PySide2.QtGui import QColor, QPainter, QTextFormat, QTextCursor, QTextDocument, QFont
from PySide2.QtCore import Qt, Signal, QSize, QRect, QRegExp


CONFIG_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'editor.json')


class Editor(QPlainTextEdit):
    returnPressed = Signal()
    requestCloseFile = Signal()
    requestOpenLastFile = Signal()
    requestOpenFile = Signal()
    requestReloadFile = Signal()
    requestSaveFile = Signal()
    requestSaveAsFile = Signal()
    requestSaveAll = Signal()
    requestSearch = Signal()
    requestCreateFile = Signal()

    class LineNumberArea(QWidget):
        def __init__(self, editor=None):
            QWidget.__init__(self, editor)
            self._editor = editor

        def sizeHint(self):
            return QSize(self._editor.get_line_number_area_width(), 0)

        def paintEvent(self, event):
            self._editor.line_numer_area_paint_event(event)

    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)

        self._editor_config = {}

        self._search_current_state = ''
        self._search_current_value = []
        self._search_current_index = -1

        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.line_number_area = Editor.LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.update_line_number_area_width()

        self.highlight_current_line()

        self.reload_config()

        self.updateRequest.connect(self.update_line_number_area)

    def setFont(self, font):
        self.edit.document().setDefaultFont(font)
        self.edit.setFont(font)
        super(BaseConsole, self).setFont(font)

    def eventFilter(self, edit, event):
        if event.type() == QEvent.KeyPress:
            return bool(self._filter_keyPressEvent(event))

        elif event.type() == QEvent.MouseButtonPress:
            return bool(self._filter_mousePressEvent(event))

        else:
            return False

    def reload_config(self, filename=None):
        self._editor_config = {}
        filename = filename if filename else CONFIG_FILENAME
        if os.path.exists(filename):
            with open(filename, 'r') as io:
                try:
                    self._editor_config = json.load(io)

                except:
                    self._editor_config = {}

        self.setTabStopWidth(self.fontMetrics().width(" " * self._editor_config.get('indent_space_count', 4)))
        font = self._editor_config.get('font')
        if font:
            font = QFont(font)
            font.setFixedPitch(True)
            self.setFont(font)

        font_size = self._editor_config.get('font_size', -1)
        if font_size > 0:
            font = self.font()
            font.setPointSize(font_size)
            self.setFont(font)

    def get_color_from_config(self, key):
        color_data = self._editor_config.get('color', {})
        return QColor(color_data.get(key, 'black'))

    def get_indent_line_size(self, line):
        indent = 0
        sub_count = 0
        indent_end = 0
        for ch in line:
            if ch == "\t":
                indent += 1
                sub_count = 0
                indent_end += 1

            elif ch == " ":
                sub_count += 1
                indent_end += 1

                if sub_count == self._editor_config.get('indent_space_count', 4):
                    sub_count = 0
                    indent += 1

            else:
                break

        return indent

    def get_indent_line_info(self, line):
        space_count = 0
        tab_count = 0
        for ch in line:
            if ch == "\t":
                tab_count += 1

            elif ch == " ":
                space_count += 1

            else:
                break

        indent_space_count = self._editor_config.get('indent_space_count', 4)
        indent_end = tab_count + space_count
        indent = tab_count + (space_count / indent_space_count)
        real_indent_end = tab_count + ((space_count / indent_space_count) * indent_space_count)
        need_to_indent = indent_end - real_indent_end

        return int(indent), int(indent_end), int(real_indent_end), int(need_to_indent)

    def get_indent_symbol(self):
        indent_symbol = "\t"
        if self._editor_config.get('indent_space_use'):
            indent_symbol = " " * self._editor_config.get('indent_space_count', 4)

        return indent_symbol

    def get_indent_strip_line(self, line):
        result = ""
        is_char = False
        for ch in line:
            if not is_char:
                if ch != "\t" and ch != " ":
                    is_char = True

            else:
                result += ch

        return result

    def selected_text(self):
        cursor = self.textCursor()
        text = cursor.selectedText()
        text = text.replace(u"\u2029", "\n")
        text = text.replace(u"\u2028", "\n")
        while text.startswith("\n"):
            text = text[1:]

        while text.endswith("\n"):
            text = text[:-1]

        return text

    def line_numer_area_paint_event(self, event):
        if self._editor_config.get('draw_line_number'):
            painter = QPainter(self.line_number_area)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(event.rect(), self.get_color_from_config("line_number_background"))
            painter.setPen(self.get_color_from_config("line_number"))

            block = self.firstVisibleBlock()
            block_number = block.blockNumber()
            top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
            bottom = top + self.blockBoundingRect(block).height()

            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    number = str(block_number + 1)
                    painter.drawText(0, top, self.line_number_area.width(), self.fontMetrics().height(), Qt.AlignRight,
                                     number)

                block = block.next()
                top = bottom
                bottom = top + self.blockBoundingRect(block).height()
                block_number += 1

    def get_line_number_area_width(self):
        digits = 1
        last = max(1, self.blockCount())
        while last >= 10:
            last /= 10
            digits += 1

        space = 3 + self.fontMetrics().width("9") * digits
        return space

    def resizeEvent(self, event):
        QPlainTextEdit.resizeEvent(self, event)
        content_rect = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(content_rect.left(), content_rect.top(), self.get_line_number_area_width(), content_rect.height()))

    def update_line_number_area_width(self):
        self.setViewportMargins(self.get_line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, number):
        if number:
            self.line_number_area.scroll(0, number)

        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def highlight_current_line(self):
        selection_list = []
        if self._editor_config.get('draw_line_highlight'):
            selection = QTextEdit.ExtraSelection()
            line_color = self.get_color_from_config("highlight_selected_line")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selection_list.append(selection)

        selection_list.extend(self._search_current_value)
        self.setExtraSelections(selection_list)

    def search(self, text, match_case=False, whole_word=False, regular=False, backward=False, wrap=False):
        flags = 0
        if backward:
            flags |= QTextDocument.FindBackward

        if match_case:
            flags |= QTextDocument.FindCaseSensitively

        if whole_word:
            flags |= QTextDocument.FindWholeWords

        if regular:
            text = QRegExp(text)

        if wrap:
            self.moveCursor(QTextCursor.Start)

        extra_selection_list = []
        color = self.get_color_from_config("highlight_find_word")
        count = 0
        while self.find(text):
            extra = QTextEdit.ExtraSelection()
            extra.format.setBackground(color)

            extra.cursor = self.textCursor()
            extra_selection_list.append(extra)
            count += 1

        self.setExtraSelections(extra_selection_list)

        search_current_state = '{}{}{}'.format(hash(text), hash(flags), hash(regular))
        search_current_continue = (
            self._search_current_state == search_current_state
            and self._search_current_index < len(extra_selection_list)
        )
        self._search_current_state = search_current_state
        self._search_current_value = extra_selection_list
        self._search_current_index = -1 if not search_current_continue else self._search_current_index

        self.search_next()

    def search_reset(self):
        self._search_current_state = ''
        self._search_current_value = []
        self._search_current_index = -1
        self.setExtraSelections([])

    def search_prev(self):
        self._search_current_index -= 1
        if self._search_current_index < 0:
            self._search_current_index = len(self._search_current_value) - 1

        self.search_select_current()
    
    def search_next(self):
        self._search_current_index += 1
        if self._search_current_index >= len(self._search_current_value):
            self._search_current_index = 0

        self.search_select_current()

    def search_select_current(self):
        current = self._search_current_value[self._search_current_index]
        line = current.cursor.blockNumber() + 1
        column = current.cursor.columnNumber()
        self.search_select_line(line, column)

    def search_select_line(self, line, column=0):
        cursor = QTextCursor(self.document().findBlockByLineNumber(line - 1))
        cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, column)
        self.setTextCursor(cursor)

    def enter(self):
        indent_symbol = self.get_indent_symbol()
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()

        previous_pos = cursor.position()
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        offset_pos = cursor.position()
        line = cursor.selectedText()
        cursor.setPosition(previous_pos)
        offset = offset_pos - previous_pos
        if offset > 0:
            line = line[:-offset]

        if line:
            indent = self.get_indent_line_size(line)
            if line[-1] == ":":
                cursor.insertText("\n" + (indent_symbol * (indent + 1)))

            else:
                cursor.insertText("\n" + (indent_symbol * indent))

        else:
            cursor.insertText("\n")

        self.setTextCursor(cursor)

    def update_current_line_indent(self, value):
        indent_symbol = self.get_indent_symbol()
        indent_space_count = self._editor_config.get('indent_space_count', 4)
        cursor = self.textCursor()
        position = cursor.position()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        abs_start = cursor.selectionStart()
        abs_end = cursor.selectionEnd()
        text = cursor.selectedText()
        text = text.replace(u"\u2029", "\n")
        text = text.replace(u"\u2028", "\n")
        text = str(text)
        if text.count("\n") == 0 and (abs_start != start or abs_end != end or start == end):
            # single selection add indent.
            indent, indent_end, real_indent_end, need_to_indent = self.get_indent_line_info(text)
            relative_position = start - abs_start
            indent_offset = indent_space_count - (len(text[real_indent_end:relative_position] % indent_space_count))
            if relative_position > indent_end:
                less_offset = indent_space_count - indent_offset
                if less_offset == 0:
                    less_offset += indent_space_count

                less_position = position - less_offset
                if less_position < 0:
                    less_position = 0

                cursor.setPosition(less_position)

            else:
                if need_to_indent > 0 and value < 0:
                    indent += 1

                cursor.setPosition(abs_start)
                cursor.setPosition(abs_start + indent_end, QTextCursor.KeepAnchor)
                cursor.insertText(indent_symbol * (indent + value))

        else:
            # multiline add indent.
            replace_text = []
            line_number = 0
            for line in text.splitlines():
                indent = self.get_indent_line_size(line)
                line = self.get_indent_strip_line(line)
                replace_text.append(indent_symbol * (indent + value) + line)
                line_number += 1

            replace_text = "\n".join(replace_text)
            cursor.insertText(replace_text)
            cursor.setPosition(abs_start)
            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
            for l in range(line_number - 1):
                cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor)

            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)

        self.setTextCursor(cursor)

    def move_line(self, value):
        cursor = self.textCursor()
        position = cursor.position()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()

        else:
            start = cursor.position()
            end = start

        # get full line.
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)

        # get information about selection.
        source_start = cursor.selectionStart()
        source_end = cursor.selectionEnd()
        source_text = cursor.selectedText()

        previous_position = cursor.position()
        if value > 0:
            cursor.setPosition(end)
            cursor.movePosition(QTextCursor.Down)

        else:
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.Up)

        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        target_position = cursor.position()
        if target_position == previous_position:
            if position < end:
                cursor.setPosition(end)
                cursor.setPosition(start, QTextCursor.KeepAnchor)

            else:
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.KeepAnchor)

        else:
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            target_text = cursor.selectedText()

            cursor.beginEditBlock()

            # replace selected lines to next line.
            cursor.setPosition(source_start)
            cursor.setPosition(source_end, QTextCursor.KeepAnchor)
            cursor.insertText(target_text)
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            current_start = cursor.selectionStart()
            current_end = cursor.selectionEnd()

            if value > 0:
                cursor.setPosition(current_end)
                cursor.movePosition(QTextCursor.Down)

            else:
                cursor.setPosition(current_start)
                cursor.movePosition(QTextCursor.Up)

            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            selection_start_position = cursor.selectionStart()
            cursor.insertText(source_text)
            selection_end_position = selection_start_position + (source_end - source_start)
            cursor.setPosition(selection_start_position)
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.setPosition(selection_end_position, QTextCursor.KeepAnchor)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            cursor.endEditBlock()

        self.setTextCursor(cursor)

    def move_current_line_up(self):
        self.move_line(-1)

    def move_curent_line_down(self):
        self.move_line(1)

    def add_current_line_indent(self):
        self.update_current_line_indent(1)

    def remove_current_line_indent(self):
        self.update_current_line_indent(-1)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and QApplication.keyboardModifiers() == Qt.ControlModifier:
            self.returnPressed.emit()
            event.accept()

        else:
            if event.key() == Qt.Key_Return:
                self.enter()

            elif event.key() == Qt.Key_Tab:
                self.add_current_line_indent()

            elif event.key() == Qt.Key_Backtab:
                self.remove_current_line_indent()

            elif event.key() == Qt.Key_Up and QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
                self.move_current_line_up()

            elif event.key() == Qt.Key_Down and QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
                self.move_curent_line_down()

            elif event.key() == Qt.Key_W and QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.requestCloseFile.emit()

            elif event.key() == Qt.Key_T and QApplication.keyboardModifiers() == (
                    Qt.ControlModifier | Qt.ShiftModifier):
                self.requestOpenLastFile.emit()

            elif event.key() == Qt.Key_R and QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
                self.requestReloadFile.emit()

            elif event.key() == Qt.Key_O and QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.requestOpenFile.emit()

            elif event.key() == Qt.Key_S and QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.requestSaveFile.emit()

            elif event.key() == Qt.Key_S and QApplication.keyboardModifiers() == Qt.AltModifier:
                self.requestSaveAsFile.emit()

            elif event.key() == Qt.Key_S and QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
                self.requestSaveAll.emit()

            elif event.key() == Qt.Key_F and QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.requestSearch.emit()

            elif event.key() == Qt.Key_N and QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.requestCreateFile.emit()

            else:
                super(Editor, self).keyPressEvent(event)
