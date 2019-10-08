from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

from . import line_number_area, syntax_highlighter


class EditorWindow(QtGui.QPlainTextEdit):
    returnPressed = QtCore.Signal()
    closeRequested = QtCore.Signal()
    restoreLastClosedRequested = QtCore.Signal()
    reloadRequested = QtCore.Signal()
    openRequested = QtCore.Signal()
    saveRequested = QtCore.Signal()
    saveAsRequested = QtCore.Signal()
    saveAllRequested = QtCore.Signal()
    searchRequested = QtCore.Signal()
    newFileRequested = QtCore.Signal()

    SAVE_HISTORY = False
    DRAW_LINE_NUMBER = True
    INDENT_DRAW = True
    INDENT_SPACE_COUNT = 4
    INDENT_DRAW_WIDTH = 0.5
    INDENT_REPLACE_SPACE = True
    HIGHLIGHT_SELECTED_LINE = True

    COLOR_MAP = {
        "background": Qt4Gui.QColor("#A88627"),
        "line_number": QtCore.Qt.black,
        "line_number_background": Qt4Gui.QColor("#5C5C5C"),
        "indent": QtCore.Qt.white,
        "highlight_selected_line": Qt4Gui.QColor("#4D4225"),
        "highlight_selected": Qt4Gui.QColor("#665526"),
        "highlight_find_word": Qt4Gui.QColor(QtCore.Qt.gray).lighter(130),
        "highlight_similiar_word": Qt4Gui.QColor(QtCore.Qt.gray).lighter(130),
    }

    @staticmethod
    def GetColor(key):

        """
        Get color by given key.
        """

        if key in EditorWindow.COLOR_MAP:
            return EditorWindow.COLOR_MAP[key]
        else:
            return Qt4Gui.QColor("#black")

    @staticmethod
    def LineIndent(line):

        """
        Get line indent.
        """

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

                if sub_count == EditorWindow.INDENT_SPACE_COUNT:
                    sub_count = 0
                    indent += 1

            else:
                sub_count = 0
                break

        return indent

    @staticmethod
    def LineIndentInfo(line):

        """
        Get line indent info.
        """

        space_count = 0
        tab_count = 0
        for ch in line:
            if ch == "\t":
                tab_count += 1

            elif ch == " ":
                space_count += 1

            else:
                break

        indent_end = tab_count + space_count
        indent = tab_count + (space_count / EditorWindow.INDENT_SPACE_COUNT)
        real_indent_end = tab_count + ((space_count / EditorWindow.INDENT_SPACE_COUNT) * EditorWindow.INDENT_SPACE_COUNT)
        need_to_indent = indent_end - real_indent_end

        return indent, indent_end, real_indent_end, need_to_indent

    @staticmethod
    def GetIndentSymbol():

        """
        Get indent character.
        """

        indent_symbol = "\t"
        if EditorWindow.INDENT_REPLACE_SPACE:
            indent_symbol = " " * EditorWindow.INDENT_SPACE_COUNT

        return indent_symbol

    @staticmethod
    def LineWithoutIndent(line):

        """
        Get line without indnt.
        """

        result = ""
        breaked = False
        for ch in line:
            if ch != "\t":
                if ch != " ":
                    breaked = True

            if breaked:
                result += ch

        return result

    def __init__(self, parent=None):

        """
        Initialize default settings.
        """

        QtGui.QPlainTextEdit.__init__(self, parent)

        self._line_area = line_number_area.LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        self.setTabStopWidth(self.fontMetrics().width(" " * EditorWindow.INDENT_SPACE_COUNT))
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        self._highlight_handle = syntax_highlighter.SyntaxHighlighter(self.document())

    def selectedText(self):

        """
        Get selected text.
        """

        cursor = self.textCursor()
        text = cursor.selectedText()
        text = text.replace(u"\u2029", "\n")
        text = text.replace(u"\u2028", "\n")
        # text = unicode(text)
        while text.startswith("\n"):
            text = text[1:]
        while text.endswith("\n"):
            text = text[:-1]
        return text

    def lineNumberAreaPaintEvent(self, event):

        """
        Line number area paint event.
        """

        if EditorWindow.DRAW_LINE_NUMBER:
            painter = Qt4Gui.QPainter(self._line_area)
            painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
            painter.fillRect(event.rect(), EditorWindow.GetColor("line_number_background"))
            painter.setPen(EditorWindow.GetColor("line_number"))

            block = self.firstVisibleBlock()
            block_number = block.blockNumber()
            top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
            bottom = top + self.blockBoundingRect(block).height()

            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    number = unicode(block_number + 1)
                    painter.drawText(0, top, self._line_area.width(), self.fontMetrics().height(), QtCore.Qt.AlignRight,
                                     number)

                block = block.next()
                top = bottom
                bottom = top + self.blockBoundingRect(block).height()
                block_number += 1

    def lineNumberAreaWidth(self):

        """
        Get line number area size.
        """

        digits = 1
        last = max(1, self.blockCount())
        while last >= 10:
            last /= 10
            digits += 1

        space = 3 + self.fontMetrics().width("9") * digits
        return space

    def resizeEvent(self, event):

        """
        Resize event.
        """

        QtGui.QPlainTextEdit.resizeEvent(self, event)
        content_rect = self.contentsRect()
        self._line_area.setGeometry(
            QtCore.QRect(content_rect.left(), content_rect.top(), self.lineNumberAreaWidth(), content_rect.height()))

    def updateLineNumberAreaWidth(self, block_count):

        """
        Update line number area size.
        """

        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def highlightCurrentLine(self):

        """
        Highlight current line.
        """

        if EditorWindow.HIGHLIGHT_SELECTED_LINE:
            selection_list = []
            selection = QtGui.QTextEdit.ExtraSelection()
            line_color = EditorWindow.GetColor("highlight_selected_line")
            selection.format.setBackground(line_color)
            selection.format.setProperty(Qt4Gui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selection_list.append(selection)
            self.setExtraSelections(selection_list)

    def updateLineNumberArea(self, rect, number):

        """
        Update line number area.
        """

        if number:
            self._line_area.scroll(0, number)
        else:
            self._line_area.update(0, rect.y(), self._line_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def search(self, text, matchCase=False, completeWord=False, regEnabled=False, up=False, wrap=False):

        """
        Search text.
        """

        flags = None
        if up:
            if not flags:
                flags = QtGui.QTextDocument.FindBackward
            else:
                flags |= QtGui.QTextDocument.FindBackward
        if matchCase:
            if not flags:
                flags = QtGui.QTextDocument.FindCaseSensitively
            else:
                flags |= QtGui.QTextDocument.FindCaseSensitively
        if completeWord:
            if not flags:
                flags = QtGui.QTextDocument.FindWholeWords
            else:
                flags |= QtGui.QTextDocument.FindWholeWords
        color = self.GetColor("highlight_find_word")
        cursor = self.textCursor()
        extraSelections = []
        if flags:
            _search = lambda _text: self.find(_text, flags)
        else:
            _search = lambda _text: self.find(_text)
        if wrap:
            self.moveCursor(Qt4Gui.QTextCursor.Start)
        count = 0
        first_occur = None
        while _search(text):
            extra = QtGui.QTextEdit.ExtraSelection()
            extra.format.setBackground(color)
            if first_occur is None:
                first_occur = self.textCursor()
            extra.cursor = self.textCursor()
            extraSelections.append(extra)
            count += 1

        self.setExtraSelections(extraSelections)
        if first_occur is not None:
            self.setTextCursor(first_occur)

    def enter(self):

        """
        Enter event.
        """

        indent_symbol = self.GetIndentSymbol()
        cursor = self.textCursor()
        position = cursor.position()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        previous_pos = cursor.position()
        cursor.movePosition(Qt4Gui.QTextCursor.StartOfLine)
        cursor.movePosition(Qt4Gui.QTextCursor.EndOfLine, Qt4Gui.QTextCursor.KeepAnchor)
        offset_pos = cursor.position()
        line = cursor.selectedText()
        cursor.setPosition(previous_pos)
        offset = offset_pos - previous_pos
        if offset > 0:
            line = line[:-offset]
        if line:
            indent = self.LineIndent(line)
            if line[-1] == ":":
                cursor.insertText("\n" + (indent_symbol * (indent + 1)))
            else:
                cursor.insertText("\n" + (indent_symbol * (indent)))
        else:
            cursor.insertText("\n")
        self.setTextCursor(cursor)

    def updateIndent(self, value):

        """
        Update indent.
        """

        indent_symbol = self.GetIndentSymbol()
        cursor = self.textCursor()
        position = cursor.position()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(Qt4Gui.QTextCursor.StartOfLine)
        cursor.setPosition(end, Qt4Gui.QTextCursor.KeepAnchor)
        cursor.movePosition(Qt4Gui.QTextCursor.EndOfLine, Qt4Gui.QTextCursor.KeepAnchor)
        abs_start = cursor.selectionStart()
        abs_end = cursor.selectionEnd()
        text = cursor.selectedText()
        text = text.replace(u"\u2029", "\n")
        text = text.replace(u"\u2028", "\n")
        text = str(text)
        if text.count("\n") == 0 and (abs_start != start or abs_end != end or start == end):
            # Single selection add indent.
            indent, indent_end, real_indent_end, need_to_indent = self.LineIndentInfo(text)
            relative_position = start - abs_start
            indent_offset = self.INDENT_SPACE_COUNT - (
            (len(text[real_indent_end:relative_position]) % self.INDENT_SPACE_COUNT))
            if relative_position > indent_end:
                less_offset = self.INDENT_SPACE_COUNT - indent_offset
                if less_offset == 0:
                    less_offset += self.INDENT_SPACE_COUNT
                less_position = position - less_offset
                if less_position < 0:
                    less_position = 0
                cursor.setPosition(less_position)
            else:
                if need_to_indent > 0 and value < 0:
                    indent += 1
                cursor.setPosition(abs_start)
                cursor.setPosition(abs_start + indent_end, Qt4Gui.QTextCursor.KeepAnchor)
                cursor.insertText(indent_symbol * (indent + value))
        else:
            # Muliline add indent.
            replace_text = []
            line_number = 0
            for line in text.splitlines():
                indent = self.LineIndent(line)
                line = self.LineWithoutIndent(line)
                replace_text.append(indent_symbol * (indent + value) + line)
                line_number += 1
            replace_text = "\n".join(replace_text)
            cursor.insertText(replace_text)
            cursor.setPosition(abs_start)
            cursor.movePosition(Qt4Gui.QTextCursor.StartOfLine, Qt4Gui.QTextCursor.MoveAnchor)
            for l in xrange(line_number - 1):
                cursor.movePosition(Qt4Gui.QTextCursor.Down, Qt4Gui.QTextCursor.KeepAnchor)
            cursor.movePosition(Qt4Gui.QTextCursor.EndOfLine, Qt4Gui.QTextCursor.KeepAnchor)

        self.setTextCursor(cursor)

    def updateLinePosition(self, value):

        """
        Update line position.
        """

        cursor = self.textCursor()
        position = cursor.position()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
        else:
            start = cursor.position()
            end = start

        # Get full line.
        cursor.setPosition(start)
        cursor.movePosition(Qt4Gui.QTextCursor.StartOfLine)
        cursor.setPosition(end, Qt4Gui.QTextCursor.KeepAnchor)
        cursor.movePosition(Qt4Gui.QTextCursor.EndOfLine, Qt4Gui.QTextCursor.KeepAnchor)

        # Get information about selection.
        source_start = cursor.selectionStart()
        source_end = cursor.selectionEnd()
        source_text = cursor.selectedText()

        previous_position = cursor.position()
        if value > 0:
            cursor.setPosition(end)
            cursor.movePosition(Qt4Gui.QTextCursor.Down)
        else:
            cursor.setPosition(start)
            cursor.movePosition(Qt4Gui.QTextCursor.Up)

        cursor.movePosition(Qt4Gui.QTextCursor.StartOfLine)
        cursor.movePosition(Qt4Gui.QTextCursor.EndOfLine, Qt4Gui.QTextCursor.KeepAnchor)
        target_position = cursor.position()
        if target_position == previous_position:
            if position < end:
                cursor.setPosition(end)
                cursor.setPosition(start, Qt4Gui.QTextCursor.KeepAnchor)
            else:
                cursor.setPosition(start)
                cursor.setPosition(end, Qt4Gui.QTextCursor.KeepAnchor)
        else:
            cursor.movePosition(Qt4Gui.QTextCursor.StartOfLine)
            cursor.movePosition(Qt4Gui.QTextCursor.EndOfLine, Qt4Gui.QTextCursor.KeepAnchor)
            target_start = cursor.selectionStart()
            target_end = cursor.selectionEnd()
            target_text = cursor.selectedText()

            cursor.beginEditBlock()

            # Replace selected lines to next line.
            cursor.setPosition(source_start)
            cursor.setPosition(source_end, Qt4Gui.QTextCursor.KeepAnchor)
            cursor.insertText(target_text)
            cursor.movePosition(Qt4Gui.QTextCursor.StartOfLine)
            cursor.movePosition(Qt4Gui.QTextCursor.EndOfLine, Qt4Gui.QTextCursor.KeepAnchor)
            current_start = cursor.selectionStart()
            current_end = cursor.selectionEnd()

            if value > 0:
                cursor.setPosition(current_end)
                cursor.movePosition(Qt4Gui.QTextCursor.Down)
            else:
                cursor.setPosition(current_start)
                cursor.movePosition(Qt4Gui.QTextCursor.Up)

            cursor.movePosition(Qt4Gui.QTextCursor.StartOfLine)
            cursor.movePosition(Qt4Gui.QTextCursor.EndOfLine, Qt4Gui.QTextCursor.KeepAnchor)
            selection_start_position = cursor.selectionStart()
            cursor.insertText(source_text)
            selection_end_position = selection_start_position + (source_end - source_start)
            cursor.setPosition(selection_start_position)
            cursor.movePosition(Qt4Gui.QTextCursor.StartOfLine)
            cursor.setPosition(selection_end_position, Qt4Gui.QTextCursor.KeepAnchor)
            cursor.movePosition(Qt4Gui.QTextCursor.EndOfLine, Qt4Gui.QTextCursor.KeepAnchor)
            cursor.endEditBlock()

        self.setTextCursor(cursor)

    def moveLineUp(self):

        """
        Move line up.
        """

        self.updateLinePosition(-1)

    def moveLineDowm(self):

        """
        Move line down.
        """

        self.updateLinePosition(1)

    def addIndent(self):

        """
        Add line indent.
        """

        self.updateIndent(1)

    def removeIndent(self):

        """
        Remove indent.
        """

        self.updateIndent(-1)

    def keyPressEvent(self, event):

        """
        Key press event.
        """

        if event.key() == QtCore.Qt.Key_Return and QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            self.returnPressed.emit()
            event.accept()

        else:
            if event.key() == QtCore.Qt.Key_Return:
                self.enter()

            elif event.key() == QtCore.Qt.Key_Tab:
                self.addIndent()

            elif event.key() == QtCore.Qt.Key_Backtab:
                self.removeIndent()

            elif event.key() == QtCore.Qt.Key_Up and QtGui.QApplication.keyboardModifiers() == (
                    QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                self.moveLineUp()

            elif event.key() == QtCore.Qt.Key_Down and QtGui.QApplication.keyboardModifiers() == (
                    QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                self.moveLineDowm()

            elif event.key() == QtCore.Qt.Key_W and QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                self.closeRequested.emit()

            elif event.key() == QtCore.Qt.Key_T and QtGui.QApplication.keyboardModifiers() == (
                    QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                self.restoreLastClosedRequested.emit()

            elif event.key() == QtCore.Qt.Key_R and QtGui.QApplication.keyboardModifiers() == (
                    QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                self.reloadRequested.emit()

            elif event.key() == QtCore.Qt.Key_O and QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                self.openRequested.emit()

            elif event.key() == QtCore.Qt.Key_S and QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                self.saveRequested.emit()

            elif event.key() == QtCore.Qt.Key_S and QtGui.QApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
                self.saveAsRequested.emit()

            elif event.key() == QtCore.Qt.Key_S and QtGui.QApplication.keyboardModifiers() == (
                    QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                self.saveAllRequested.emit()

            elif event.key() == QtCore.Qt.Key_F and QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                self.searchRequested.emit()

            elif event.key() == QtCore.Qt.Key_N and QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
                self.newFileRequested.emit()

            else:
                super(EditorWindow, self).keyPressEvent(event)
