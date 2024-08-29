import re

from PySide2.QtWidgets import QPlainTextEdit, QTextEdit, QCompleter, QApplication
from PySide2.QtGui import QFontDatabase, QTextCursor, QBrush, QTextFormat, QPalette, QTextOption, QTextCharFormat, QPainter
from PySide2.QtCore import Qt, __version_info__ as QT_VERSION, QSignalBlocker, QRect, QRegExp, Signal, QEvent

from ..language import LanguageHighlighter
from .line_number_area import LineNumberArea
from .frame_text_attribute import FrameTextAttribute
from .fold_text_attribute import FoldTextAttribute


class BaseEditor(QPlainTextEdit):
    def __init__(self, widget=None, language='python'):
        super(BaseEditor, self).__init__(widget)

        self._auto_indentation = True
        self._auto_parentheses = True
        self._replace_tab = True
        self._replace_tab_by = ' '
        self._auto_hightlight_selection = True
        self._auto_hightlight_focus = False
        self._auto_hightlight_ignore_case = True
        self._additional_text_cursor_list = []

        self._frame_handler = FrameTextAttribute(self)
        self._fold_handler = FoldTextAttribute(self)

        self._number_area = LineNumberArea(self)
        self._highlighter = LanguageHighlighter(self.document(), language)
        self._highlighter.completer().setWidget(self)
        self._highlighter.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._highlighter.completer().activated.connect(self.insert_completion)

        self.init_document_layout_handlers()
        self.init_font()
        self.perform_connections()
        self.set_tab_size(4)

    def clear_text_cursors(self):
        self._additional_text_cursor_list = []

    def get_text_cursors(self):
        result = self._additional_text_cursor_list[:]
        not result and result.append(QTextCursor(self.textCursor()))
        return result

    def update_text_cursors(self, force_register=False):
        active_cursor = self.textCursor()
        active_position = active_cursor.position()

        # search and remove cursor
        remove_duplicate = False
        additional_text_cursor_count = len(self._additional_text_cursor_list)
        i = additional_text_cursor_count
        while i > 0:
            i -= 1
            cursor = self._additional_text_cursor_list[i]

            if cursor.position() == active_position:
                self._additional_text_cursor_list.pop(i)
                remove_duplicate = True

        # save cursor
        if not remove_duplicate or force_register:
            self._additional_text_cursor_list.append(QTextCursor(active_cursor))
            return

        # update active cursor
        if self._additional_text_cursor_list:
            self.setTextCursor(self._additional_text_cursor_list[-1])

    def language(self):
        return self._highlighter.language()

    def highligher(self):
        return self._highlighter

    def init_document_layout_handlers(self):
        self.document().documentLayout().registerHandler(
            self._frame_handler.type(),
            self._frame_handler
        )
        self.document().documentLayout().registerHandler(
            self._fold_handler.type(),
            self._fold_handler
        )

        option = QTextOption()
        option.setFlags(QTextOption.ShowTabsAndSpaces | QTextOption.IncludeTrailingSpaces)
        option.setWrapMode(QTextOption.NoWrap)
        self.document().setDefaultTextOption(option)

    def init_font(self):
        fnt = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fnt.setFixedPitch(True)
        fnt.setPointSize(10)

        self.setFont(fnt)

    def perform_connections(self):
        self.document().blockCountChanged.connect(self.update_line_number_area_width)
        self.verticalScrollBar().valueChanged.connect(self._number_area.update)
        self.cursorPositionChanged.connect(self.update_extra_selection)
        self.selectionChanged.connect(self.on_selection_changed)

    def update_style(self):
        # TODO: update on change language or style
        if self._highlighter:
            self._highlighter.rehighlight()

        if self._highlighter.style():
            current_palette = self.palette()

            # setting text format/color
            current_palette.setColor(
                QPalette.ColorRole.Text,
                self._highlighter.style().getFormat("Text").foreground().color()
            )

            # setting common background
            current_palette.setColor(
                QPalette.Base,
                self._highlighter.style().getFormat("Text").background().color()
            )

            # setting selection color
            current_palette.setColor(
                QPalette.Highlight,
                self._highlighter.style().getFormat("Selection").background().color()
            )

            self.setPalette(current_palette)

        self.update_extra_selection()

    def on_selection_changed(self):
        cursor = self.textCursor()

        selected = cursor.selectedText()

        # cursor is null if setPlainText was called.
        if cursor.isNull():
            return

        cursor.movePosition(QTextCursor.MoveOperation.Left)
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)

        blocker = QSignalBlocker(self)  # block signals until end
        self._frame_handler.clear(cursor)

        if len(selected) > 1 and cursor.selectedText() == selected:
            backup = self.textCursor()

            # perform search selecting
            self.handle_selection_query(cursor)

            self.setTextCursor(backup)

        self.update_extra_selection()

    def resizeEvent(self, e):
        super(BaseEditor, self).resizeEvent(e)
        self.update_line_geometry()

    def update_line_geometry(self):
        cr = self.contentsRect()
        self._number_area.setGeometry(
            QRect(
                cr.left(),
                cr.top(),
                self._number_area.sizeHint().width(),
                cr.height()
            )
        )

    def update_line_number_area_width(self):
        self.setViewportMargins(self._number_area.sizeHint().width(), 0, 0, 0)

    def update_line_number_area(self, rect):
        self._number_area.update(
            0,
            rect.y(),
            self._number_area.sizeHint().width(),
            rect.height()
        )
        self.update_line_geometry()

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def handle_selection_query(self, cursor):
        search_iterator = cursor
        search_iterator.movePosition(QTextCursor.Start)
        search_iterator = self.document().find(cursor.selectedText(), search_iterator)
        while search_iterator.hasSelection():
            self._frame_handler.frame(search_iterator)
            search_iterator = self.document().find(cursor.selectedText(), search_iterator)

    def fold(self):
        self._fold_handler.fold(self.textCursor())

    def unfold(self):
        self._fold_handler.unfold(self.textCursor())

    def frame(self):
        self._frame_handler.frame(self.textCursor())

    def unframe(self):
        self._frame_handler.unframe(self.textCursor())

    def update_extra_selection(self):
        extra = []

        self.highlight_current_line(extra)
        self.highlight_parenthesis(extra)
        self.highlight_search_results(extra)
        self.highlight_selected_words(extra)
        self.highlight_multi_selection(extra)

        self.setExtraSelections(extra)

    def highlight_parenthesis(self, extra_selection):
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            cursor = QTextCursor(cursor)

            current_symbol = self.char_under_cursor(cursor)
            format_type = self.get_cursor_format_type(cursor)
            is_comment = format_type in ('Comment', 'String')
            prev_symbol = self.char_under_cursor(cursor, -1)

            if is_comment:
                continue

            cursor = self.textCursor()

            pair = self._highlighter.get_parentheses(current_symbol)
            pair = pair if pair else self._highlighter.get_parentheses(prev_symbol)
            if pair:
                position = cursor.position()

                if current_symbol == pair[0] or prev_symbol == pair[0]:
                    direction = 1
                    counter_symbol = pair[1]
                    active_symbol = pair[0]
                    if prev_symbol == pair[0]:
                        position -= 1
                        cursor.setPosition(position, QTextCursor.KeepAnchor)

                elif prev_symbol == pair[1] or current_symbol == pair[1]:
                    direction = -1
                    counter_symbol = pair[0]
                    active_symbol = pair[1]
                    if prev_symbol == pair[1]:
                        position -= 1

                    else:
                        cursor.setPosition(position + 1, QTextCursor.KeepAnchor)

                counter = 1

                while counter != 0 and 0 <= position <= (self.document().characterCount() - 1):
                    # Moving position
                    position += direction

                    format_type = self.get_position_format_type(position)
                    is_comment = format_type in ('Comment', 'String')
                    if is_comment:
                        continue

                    character = self.document().characterAt(position)
                    # Checking symbol under position
                    if character == active_symbol:
                        counter += 1

                    elif character == counter_symbol:
                        counter -= 1

                fmt = self._highlighter.style().getFormat("Parentheses")

                # found
                if counter == 0:
                    direction_enum = QTextCursor.MoveOperation.Left if direction < 0 else QTextCursor.MoveOperation.Right

                    selection = QTextEdit.ExtraSelection()
                    selection.format = fmt
                    selection.cursor = cursor
                    selection.cursor.clearSelection()
                    selection.cursor.movePosition(
                        direction_enum,
                        QTextCursor.MoveMode.MoveAnchor,
                        abs(cursor.position() - position)
                    )

                    selection.cursor.movePosition(
                        QTextCursor.MoveOperation.Right,
                        QTextCursor.MoveMode.KeepAnchor,
                        1
                    )

                    extra_selection.append(selection)

                    selection = QTextEdit.ExtraSelection()
                    selection.format = fmt
                    selection.cursor = cursor
                    selection.cursor.clearSelection()
                    selection.cursor.movePosition(
                        direction_enum,
                        QTextCursor.MoveMode.KeepAnchor,
                        1
                    )

                    extra_selection.append(selection)

    def highlight_current_line(self, extra_selection):
        if not self.isReadOnly():
            for cursor in self.get_text_cursors():
                cursor = QTextCursor(cursor)

                selection = QTextEdit.ExtraSelection()
                selection.format = self._highlighter.style().getFormat("CurrentLine")
                selection.format.setForeground(QBrush())
                selection.format.setProperty(QTextFormat.FullWidthSelection,  True)
                selection.cursor = cursor
                selection.cursor.clearSelection()

                extra_selection.append(selection)

    def highlight_search_results(self, extra_selection):
        # TODO: highlight search results
        pass

    def highlight_multi_selection(self, extra_selection):
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            cursor = QTextCursor(cursor)

            selection = QTextEdit.ExtraSelection()
            selection.format = self._highlighter.style().getFormat("Selection")
            selection.cursor = cursor
            extra_selection.append(selection)

    def highlight_selected_words(self, extra_selection):
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            cursor = QTextCursor(cursor)

            pos = cursor.position()
            selection_start = cursor.selectionStart()
            selection_end = cursor.selectionEnd()

            regexp_letters = QRegExp('[^\W\d_]')
            regexp_spaces = QRegExp('[ \t]')

            if selection_start != selection_end and self.auto_hightlight_selection():
                previous_word = cursor.selectedText()
                cursor.select(QTextCursor.WordUnderCursor)
                word = cursor.selectedText()
                if not previous_word.endswith(word):
                    cursor.setPosition(selection_start, QTextCursor.KeepAnchor)
                    cursor.setPosition(selection_end - 1)
                    cursor.select(QTextCursor.WordUnderCursor)
                    word = cursor.selectedText()

                cursor.setPosition(selection_start, QTextCursor.KeepAnchor)
                cursor.setPosition(selection_end)

            elif self.auto_hightlight_focus():
                cursor.select(QTextCursor.WordUnderCursor)
                word = cursor.selectedText()
                cursor.setPosition(pos)

            else:
                word = None

            if word and regexp_letters.indexIn(word) >= 0 and regexp_spaces.indexIn(word) == -1:
                fmt = self._highlighter.style().getFormat("SelectionSearch")

                if self.auto_hightlight_ignore_case():
                    regexp = QRegExp('\\b{}\\b'.format(re.escape(word)), Qt.CaseInsensitive)

                else:
                    regexp = QRegExp('\\b{}\\b'.format(re.escape(word)))

                document = self.document()
                for i in range(document.blockCount()):
                    block = document.findBlockByNumber(i)
                    if block.isValid():
                        text = block.text()
                        regexp_pos = regexp.indexIn(text)

                        while regexp_pos != -1:
                            pos = block.position() + regexp_pos

                            selection = QTextEdit.ExtraSelection()
                            selection.format = fmt
                            selection.cursor = cursor
                            selection.cursor.clearSelection()
                            selection.cursor.setPosition(
                                pos,
                                QTextCursor.MoveMode.MoveAnchor,
                            )
                            selection.cursor.setPosition(
                                pos + regexp.matchedLength(),
                                QTextCursor.MoveMode.KeepAnchor,
                            )

                            extra_selection.append(selection)

                            regexp_pos = regexp.indexIn(text, regexp_pos + regexp.matchedLength())

    def completer_is_active(self):
        completer = self._highlighter.completer()
        return completer and self._highlighter.completer().popup().isVisible()

    def proceed_completer_begin(self, e):
        # TODO: show completer fast
        # TODO: dynamic completer update
        is_shortcut = bool(e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier))
        completer_active = self.completer_is_active()

        if e.key() in (Qt.Key_Tab, Qt.Key_Backtab, Qt.Key_Space, Qt.Key_Up, Qt.Key_Down):
            is_shortcut = True

        return not (not completer_active or not is_shortcut)

    def proceed_completer_end(self, e):
        ctrl_or_shift = e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)

        if not self._highlighter.completer() or ctrl_or_shift or e.key() == Qt.Key_Delete:
            return

        eow = r'(~!@#$%^&*()_+{}|:"<>?,./;\'[]\-=)'

        is_shortcut = ((e.modifiers() & Qt.ControlModifier) and e.key() == Qt.Key_Space)
        cursor = self.textCursor()
        completion_prefix = self.word_under_cursor(cursor)

        # TODO: realize ctrl+enter (run code) event
        # TODO: realize ctrl+o (open), ctrl+s (save), ctrl+shift+o (save as), ctrl+w (close tab), ctrl+t (open previously closed tab) event

        if not is_shortcut and (e.text() or len(completion_prefix) < 2 or e.text() and e.text()[-1] in eow):
            self._highlighter.completer().popup().hide()
            return

        if completion_prefix != self._highlighter.completer().completionPrefix():
            self._highlighter.completer().setCompletionPrefix(completion_prefix)
            self._highlighter.completer().popup().setCurrentIndex(self._highlighter.completer().completionModel().index(0, 0))

        cursor_rect = self.cursorRect()
        cursor_rect.setWidth(
            self._highlighter.completer().popup().sizeHintForColumn(0) +
            self._highlighter.completer().popup().verticalScrollBar().sizeHint().width()
        )

        self._highlighter.completer().complete(cursor_rect)

    def get_completer_source_text(self):
        cursor = self.textCursor()
        block_text = cursor.block().text()
        col = cursor.columnNumber()
        return block_text[:col]

    def get_current_line_it(self, cursor):
        start = cursor.anchor()
        end = cursor.position()

        if start > end:
            start, end = end, start

        cursor.clearSelection()

        cursor.setPosition(end)
        cursor.movePosition(QTextCursor.StartOfLine)
        end = cursor.position()

        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        start = cursor.position()

        cursor.setPosition(end)
        pos = end

        while pos >= start:
            last_pos = pos

            yield pos

            cursor.setPosition(pos)
            cursor.movePosition(QTextCursor.Up)
            cursor.movePosition(QTextCursor.StartOfLine)
            pos = cursor.position()
            if last_pos == pos:
                break

        cursor.setPosition(start)
        cursor.movePosition(
            QTextCursor.NextCharacter,
            QTextCursor.KeepAnchor,
            end - start
        )

    def move_cursor_line_down(self, cursor):
        previous_pos = cursor.position()
        block_number = cursor.blockNumber()
        cursor.movePosition(QTextCursor.Down)
        line_has_change = block_number != cursor.blockNumber()
        if line_has_change:
            return True

        else:
            cursor.setPosition(previous_pos)
            return False

    def move_cursor_line_up(self, cursor):
        previous_pos = cursor.position()
        block_number = cursor.blockNumber()
        cursor.movePosition(QTextCursor.Up)
        line_has_change = block_number != cursor.blockNumber()
        if line_has_change:
            return True

        else:
            cursor.setPosition(previous_pos)
            return False

    def check_previous_cursor_word(self, cursor):
        previous_pos = cursor.position()
        block_number = cursor.blockNumber()
        cursor.movePosition(QTextCursor.WordLeft, QTextCursor.KeepAnchor)
        line_has_change = block_number != cursor.blockNumber()
        if not line_has_change:
            word = cursor.selectedText()
            word_pos = cursor.position()
            cursor.setPosition(previous_pos)

        else:
            word = ''
            word_pos = previous_pos
            cursor.setPosition(previous_pos)

        return word_pos, word

    def check_next_cursor_word(self, cursor):
        previous_pos = cursor.position()
        block_number = cursor.blockNumber()
        cursor.movePosition(QTextCursor.WordRight, QTextCursor.KeepAnchor)
        line_has_change = block_number != cursor.blockNumber()
        if not line_has_change:
            word = cursor.selectedText()
            word_pos = cursor.position()
            cursor.setPosition(previous_pos)

        else:
            word = ''
            word_pos = previous_pos
            cursor.setPosition(previous_pos)

        return word_pos, word

    def on_comment(self, e):
        comment_symbol = self._highlighter.get_single_comment()
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            cursor.beginEditBlock()

            selection_start = cursor.selectionStart()
            selection_end = cursor.selectionEnd()

            # check comment on line
            is_comment = True
            line_count = 0
            for _ in self.get_current_line_it(cursor):
                line_count += 1
                cursor.movePosition(QTextCursor.StartOfLine)
                word_pos, word = self.check_next_cursor_word(cursor)
                if word:
                    cursor.setPosition(word_pos)
                    if comment_symbol not in word:
                        word_pos, word = self.check_next_cursor_word(cursor)
                        if comment_symbol not in word:
                            is_comment = False

            # switch comment state
            if is_comment:
                selection_start -= (len(comment_symbol) + 1)

            else:
                selection_start += (len(comment_symbol) + 1)

            for _ in self.get_current_line_it(cursor):
                cursor.movePosition(QTextCursor.StartOfLine)
                word_pos, word = self.check_next_cursor_word(cursor)
                if word:
                    word_is_empty = not bool(word.strip(' \t'))
                    cursor.setPosition(word_pos)
                    if word_is_empty:
                        word_pos, word = self.check_next_cursor_word(cursor)
                        cursor.setPosition(word_pos)

                if not is_comment:
                    cursor.setPosition(word_pos - len(word))
                    cursor.insertText(comment_symbol)
                    cursor.insertText(' ')
                    selection_end += (len(comment_symbol) + 1)

                else:
                    cursor.setPosition(word_pos - len(word), QTextCursor.KeepAnchor)
                    cursor.removeSelectedText()
                    selection_end -= (len(comment_symbol) + 1)

            if line_count <= 1:
                cursor.movePosition(QTextCursor.Down)
                cursor.movePosition(QTextCursor.StartOfLine)

            else:
                cursor.setPosition(selection_start)
                cursor.setPosition(selection_end, QTextCursor.KeepAnchor)

            cursor.endEditBlock()
            self.setTextCursor(cursor)

    def on_duplicate(self, e):
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            cursor.beginEditBlock()

            offset = cursor.positionInBlock()

            selection_begin = cursor.selectionStart()
            selection_end = cursor.selectionEnd()

            insert_at_same_line = True
            has_selection = selection_begin != selection_end
            if not has_selection:
                cursor.setPosition(selection_begin, QTextCursor.MoveAnchor)
                cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
                cursor.setPosition(selection_end, QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                insert_at_same_line = False

            text = cursor.selectedText()

            if not text:
                cursor.endEditBlock()

            else:
                if not insert_at_same_line:
                    cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.MoveAnchor)
                    cursor.insertText('\n')

                else:
                    cursor.setPosition(selection_end, QTextCursor.MoveAnchor)

                insert_begin = cursor.position()
                cursor.insertText(text)
                insert_end = cursor.position()

                if not has_selection:
                    cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
                    cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, offset)

                else:
                    cursor.setPosition(insert_begin, QTextCursor.MoveAnchor)
                    cursor.setPosition(insert_end, QTextCursor.KeepAnchor)

                cursor.endEditBlock()

            self.setTextCursor(cursor)

        self.proceed_completer_end(e)

    def on_tab(self, e):
        tab_size = self.tab_size()
        tab_symbol = ' ' * tab_size if self.tab_auto_replace() else '\t'
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            if cursor.hasSelection():
                cursor.beginEditBlock()

                selection_start = cursor.selectionStart()
                selection_end = cursor.selectionEnd()
                selection_start += tab_size

                for _ in self.get_current_line_it(cursor):
                    selection_end += tab_size
                    cursor.insertText(tab_symbol)

                cursor.endEditBlock()

                cursor.setPosition(selection_start)
                cursor.setPosition(selection_end, QTextCursor.KeepAnchor)

            else:
                if not self.completer().popup().isVisible():
                    cursor.insertText(tab_symbol)

            self.setTextCursor(cursor)

        self.proceed_completer_end(e)

    def on_backtab(self, e):
        tab_size = self.tab_size()
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            if cursor.hasSelection():
                cursor.beginEditBlock()

                selection_start = cursor.selectionStart()
                selection_end = cursor.selectionEnd()
                first_tab_size = 0

                for _ in self.get_current_line_it(cursor):
                    first_tab_size = 0
                    block_number = cursor.blockNumber()
                    cursor.movePosition(
                        QTextCursor.NextCharacter,
                        QTextCursor.KeepAnchor,
                        1
                    )
                    line_has_change = block_number != cursor.blockNumber()
                    if not line_has_change:
                        if cursor.selectedText() in '\t':
                            cursor.removeSelectedText()
                            selection_end -= 1
                            first_tab_size = 1

                        else:
                            cursor.movePosition(
                                QTextCursor.NextCharacter,
                                QTextCursor.KeepAnchor,
                                tab_size - 1
                            )
                            if cursor.selectedText() in ' ' * tab_size:
                                cursor.removeSelectedText()
                                selection_end -= tab_size
                                first_tab_size = tab_size

                selection_start -= first_tab_size
                cursor.endEditBlock()

                cursor.setPosition(selection_start)
                cursor.setPosition(selection_end, QTextCursor.KeepAnchor)

            else:
                cursor.clearSelection()
                cursor.movePosition(QTextCursor.StartOfBlock)

                for _ in range(tab_size):
                    block_number = cursor.blockNumber()
                    cursor.movePosition(
                        QTextCursor.NextCharacter,
                        QTextCursor.KeepAnchor,
                        1
                    )
                    line_is_change = block_number != cursor.blockNumber()
                    selected_text = cursor.selectedText()
                    if line_is_change:
                        break

                    if not selected_text.endswith(' ') and not selected_text.endswith('\t'):
                        cursor.movePosition(
                            QTextCursor.PreviousCharacter,
                            QTextCursor.KeepAnchor,
                            1
                        )
                        break

                    elif selected_text.endswith('\t'):
                        break

                cursor.removeSelectedText()

            self.setTextCursor(cursor)

        self.proceed_completer_end(e)

    def on_up(self, e):
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            cursor.beginEditBlock()

            offset = cursor.positionInBlock()

            selection_begin = cursor.selectionStart()
            selection_end = cursor.selectionEnd()

            cursor.setPosition(selection_begin, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
            cursor.setPosition(selection_end, QTextCursor.KeepAnchor)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            check_line = cursor.position()
            selection_offset_begin = selection_begin - check_line
            selection_offset_end = selection_end - check_line
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor)
            check_line = check_line == cursor.position()

            has_selection = selection_begin != selection_end
            text = cursor.selectedText()

            if not text:
                cursor.endEditBlock()

            else:
                cursor.removeSelectedText()

                cursor.movePosition(QTextCursor.Up, QTextCursor.MoveAnchor)

                cursor.insertText(text)
                check_line and cursor.insertText('\n')

                if not has_selection:
                    cursor.movePosition(QTextCursor.Up, QTextCursor.MoveAnchor)
                    cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
                    cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, offset)

                else:
                    cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
                    pos = cursor.position()
                    cursor.setPosition(pos + selection_offset_begin - 1, QTextCursor.MoveAnchor)
                    cursor.setPosition(pos + selection_offset_end - 1, QTextCursor.KeepAnchor)

                cursor.endEditBlock()

            self.setTextCursor(cursor)

        self.proceed_completer_end(e)

    def on_down(self, e):
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            cursor.beginEditBlock()

            offset = cursor.positionInBlock()

            selection_begin = cursor.selectionStart()
            selection_end = cursor.selectionEnd()

            cursor.setPosition(selection_begin, QTextCursor.MoveAnchor)
            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
            cursor.setPosition(selection_end, QTextCursor.KeepAnchor)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            check_line = cursor.position()
            selection_offset_begin = selection_begin - check_line
            selection_offset_end = selection_end - check_line
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor)

            has_selection = selection_begin != selection_end
            text = cursor.selectedText()

            if not text:
                cursor.endEditBlock()

            else:
                cursor.removeSelectedText()

                check_line = cursor.position()
                cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor)
                check_line = check_line == cursor.position()

                check_line and cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.MoveAnchor)
                check_line and cursor.insertText('\n')

                cursor.insertText(text)

                if not has_selection:
                    cursor.movePosition(QTextCursor.Up, QTextCursor.MoveAnchor)
                    cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
                    cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, offset)

                else:
                    cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
                    pos = cursor.position()
                    cursor.setPosition(pos + selection_offset_begin - 1, QTextCursor.MoveAnchor)
                    cursor.setPosition(pos + selection_offset_end - 1, QTextCursor.KeepAnchor)

                cursor.endEditBlock()

            self.setTextCursor(cursor)

        self.proceed_completer_end(e)

    def on_backspace(self, e):
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            position_in_block = cursor.positionInBlock()
            previous_text = cursor.block().text()[:position_in_block]
            next_text = cursor.block().text()[position_in_block:]
            if previous_text.strip() == '':
                # remove tabulation
                cursor.beginEditBlock()
                move_left = (cursor.columnNumber()) % 4
                if cursor.positionInBlock() == 0:
                    move_left = 1

                else:
                    if move_left == 0:
                        move_left = 4

                for _ in range(move_left):
                    cursor.deletePreviousChar()

                cursor.endEditBlock()
                continue

            else:
                # remove parentheses
                pair = self._highlighter.get_parentheses(previous_text[-1])
                format_type, format_pos, format_size = self.get_cursor_format(cursor)
                allow_pair = False
                if format_type not in ('Comment', 'String'):
                    allow_pair = True

                elif format_type == 'String' and format_pos == position_in_block - 1:
                    allow_pair = True

                if pair and allow_pair:
                    if pair[1] and previous_text[-1] == pair[0] and next_text and next_text == pair[1]:
                        cursor.beginEditBlock()
                        cursor.setPosition(cursor.position() + 1)
                        cursor.setPosition(cursor.position() - 2, QTextCursor.KeepAnchor)
                        cursor.removeSelectedText()
                        cursor.endEditBlock()
                        continue

            # default event
            self.setTextCursor(cursor)
            super(BaseEditor, self).keyPressEvent(e)

        self.proceed_completer_end(e)

    def on_new_line(self, e):
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            if self.auto_indentation():
                default_indent = self.get_default_indent()
                indent = self.get_current_indent(cursor)
                tab_counts = self.get_current_indent(cursor, as_tabs=True)

                format_type = self.get_cursor_format_type(cursor)
                has_next_text = self.cursor_has_next_text(cursor)
                is_comment = format_type in ('Comment',)
                is_string = format_type in ('String',)

                prev_char = self.char_under_cursor(cursor, -1)
                super(BaseEditor, self).keyPressEvent(e)

                next_char = self.char_under_cursor(cursor)
                if not is_comment and not is_string and self._highlighter.is_parentheses(prev_char, next_char):
                    if QT_VERSION >= (5, 0, 0):
                        tab_counts = indent * int(self.fontMetrics().averageCharWidth() / self.tabStopDistance())

                    else:
                        tab_counts = indent * int(self.fontMetrics().averageCharWidth() / self.tabStopWidth())

                    chars_back = 0

                    if self.tab_auto_replace():
                        cursor.insertText(' ' * (indent + default_indent))

                    else:
                        cursor.insertText('\t' * (tab_counts + 1))

                    cursor.insertText("\n")
                    chars_back += 1

                    if self.tab_auto_replace():
                        cursor.insertText(' ' * indent)
                        chars_back += indent

                    else:
                        cursor.insertText('\t' * tab_counts)
                        chars_back += tab_counts

                    while chars_back:
                        cursor.movePosition(QTextCursor.MoveOperation.Left)
                        chars_back -= 1

                else:
                    if self.tab_auto_replace():
                        cursor.insertText(' ' * indent)

                    else:
                        cursor.insertText('\t' * tab_counts)

                    if is_comment and has_next_text:
                        comment = self._highlighter.get_single_comment()
                        cursor.insertText(comment)

                self.setTextCursor(cursor)

            else:
                super(BaseEditor, self).keyPressEvent(e)

        self.proceed_completer_end(e)

    def cursor_has_next_text(self, cursor):
        pos = cursor.position()
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        result = cursor.selectedText()
        cursor.setPosition(pos)
        return len(result.strip(' \t'))

    def get_position_format_type(self, pos):
        cursor = self.textCursor()
        previous_pos = cursor.position()
        cursor.setPosition(pos)
        block = cursor.block()
        block_data = block.userData().value
        block_data = block_data if block_data else []
        block_pos = cursor.positionInBlock()
        cursor_format_type = None
        for format_start, format_length, format_type in block_data:
            if format_start <= block_pos <= format_start + format_length:
                cursor_format_type = format_type
                break

        cursor.setPosition(previous_pos)
        return cursor_format_type

    def get_cursor_format(self, cursor):
        block = cursor.block()
        block_data = block.userData().value
        block_data = block_data if block_data else []
        block_pos = cursor.positionInBlock()
        cursor_format = None, None, None
        for format_start, format_length, format_type in block_data:
            if format_start <= block_pos <= format_start + format_length:
                cursor_format = format_type, format_start, format_length
                break

        return cursor_format

    def get_cursor_format_type(self, cursor):
        block = cursor.block()
        block_data = block.userData().value
        block_data = block_data if block_data else []
        block_pos = cursor.positionInBlock()
        cursor_format_type = None
        for format_start, format_length, format_type in block_data:
            if format_start <= block_pos <= format_start + format_length:
                cursor_format_type = format_type
                break

        return cursor_format_type

    def insert_parentheses_event(self, e):
        if self.auto_parentheses():
            base_cursor = self.textCursor()
            cursor_list = self.get_text_cursors()
            for cursor in cursor_list:
                pair = self._highlighter.get_parentheses(e.text())
                format_type = self.get_cursor_format_type(cursor)
                allow_pair = format_type not in ('Comment', 'String')
                if pair and allow_pair:
                    if pair[1] and e.text() == pair[0]:
                        # inserting closed brace
                        cursor.insertText(pair[1])
                        cursor.movePosition(QTextCursor.MoveOperation.Left)

                    else:
                        # only move cursor
                        block = cursor.block()
                        pos = cursor.positionInBlock() - 1
                        pos = pos if pos >= 0 else 0
                        text = block.text()
                        if (
                            text
                            and 0 <= pos < len(text) - 1
                            and text[pos] == pair[1]
                        ):
                            cursor.movePosition(QTextCursor.MoveOperation.Right)

            self.setTextCursor(base_cursor)

        self.proceed_completer_end(e)

    def mousePressEvent(self, e):
        ctrl_and_shift = QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier)
        cleanup_cursor = False
        update_cursor = False
        if e.type() == QEvent.MouseButtonPress:
            if e.button() == Qt.LeftButton and ctrl_and_shift:
                update_cursor = True

            elif e.button() == Qt.LeftButton:
                cleanup_cursor = True

        update_cursor and self.update_text_cursors(force_register=True)  # save previous cursor

        super(BaseEditor, self).mousePressEvent(e)

        update_cursor and self.update_text_cursors()  # update cursor list
        cleanup_cursor and self.clear_text_cursors()

    def keyPressEvent(self, e):
        completer_skip = self.proceed_completer_begin(e)

        cursor_list = self.get_text_cursors()
        cursor_pos_list = [[cursor.position(), cursor.anchor(), cursor] for cursor in cursor_list]
        cursor_pos_list.sort(key=lambda item: item[1])

        if (
            e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter
        ):
            return self.on_new_line(e)

        if not completer_skip:
            ctrl_and_shift = e.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier)
            ctrl = e.modifiers() == Qt.ControlModifier
            shift = e.modifiers() == Qt.ShiftModifier
            if e.key() == Qt.Key_Backspace:
                return self.on_backspace(e)

            elif e.key() == Qt.Key_Backtab:
                return self.on_backtab(e)

            elif e.key() == Qt.Key_Tab:
                return self.on_tab(e)

            elif e.key() == Qt.Key_Up and ctrl_and_shift:
                return self.on_up(e)

            elif e.key() == Qt.Key_Down and ctrl_and_shift:
                return self.on_down(e)

            elif e.key() == Qt.Key_D and ctrl:
                return self.on_duplicate(e)

            elif e.key() == Qt.Key_Slash and ctrl:
                return self.on_comment(e)

            elif (ctrl_and_shift or ctrl or shift) and e.key() == Qt.Key_No:
                return True

        print('\n')                                 # TODO: remove this
        print(cursor_pos_list)                      # TODO: remove this
        print('event begin from', cursor_pos_list)  # TODO: remove this

        blocker = QSignalBlocker(self)
        offset = 0
        for i, (cursor_pos, cursor_anc, cursor) in enumerate(cursor_pos_list):
            # TODO: make correct position update
            cursor.setPosition(cursor_anc + offset)
            cursor.setPosition(cursor_pos + offset, QTextCursor.KeepAnchor)
            cursor_block_size = cursor.block().length()

            self.setTextCursor(cursor)
            super(BaseEditor, self).keyPressEvent(e)

            cursor_update = self.textCursor()
            pos, anc = cursor_update.position(), cursor_update.anchor()
            block_size = cursor.block().length()
            cursor_pos_list[i][0] = pos
            cursor_pos_list[i][1] = anc

            need_offset = (
                cursor_pos != cursor_anc
                or pos != anc
                or block_size != cursor_block_size
            )

            if need_offset:
                anc_without_offset = (anc - offset)
                offset -= min(anc_without_offset, cursor_anc) - max(anc_without_offset, cursor_anc)

            print(offset, (anc, cursor_anc), (pos, cursor_pos), (block_size, cursor_block_size))  # TODO: remove this

        for cursor_pos, cursor_anc, cursor in cursor_pos_list:
            cursor.setPosition(cursor_anc)
            cursor.setPosition(cursor_pos, QTextCursor.KeepAnchor)

        self.setTextCursor(cursor_list[-1])

        self.update_extra_selection()

        cursor_pos_list = [[cursor.position(), cursor.anchor(), cursor] for cursor in cursor_list]        # TODO: remove this
        print('event end with', cursor_pos_list)                                                          # TODO: remove this

        self.insert_parentheses_event(e)
        self.proceed_completer_end(e)

    def paintEvent(self, e):
        self.update_line_number_area(e.rect())

        cursor_list = self.get_text_cursors()
        cursor_count = len(cursor_list)
        if cursor_count <= 1:
            # process default paint event
            return super(BaseEditor, self).paintEvent(e)

        cursor_list.append(self.textCursor())

        # process default paint event
        super(BaseEditor, self).paintEvent(e)

        # process additional cursor paint event
        context = self.getPaintContext()
        cursor_is_visible = context.cursorPosition >= 0  # -1 on visibility off

        offset = self.contentOffset()
        block = self.firstVisibleBlock()

        viewport = self.viewport()
        viewport_rect = viewport.rect()
        painter = QPainter(viewport)

        cursor_width = self.cursorWidth() if cursor_is_visible else 0
        painter.setPen(context.palette.text().color())
        painter.setBrushOrigin(offset)

        event_rect = e.rect()
        max_x = offset.x() + max(viewport_rect.width(), self.maximumWidth()) - self.document().documentMargin()
        event_rect.setRight(min(event_rect.right(), max_x))
        painter.setClipRect(event_rect)

        text_editable = not self.isReadOnly() or self.textInteractionFlags() & Qt.TextSelectableByKeyboard

        need_update_viewport = False
        while block.isValid():
            rect = self.blockBoundingRect(block).translated(offset)
            layout = block.layout()
            block_position = block.position()
            block_size = block.length()
            if not block.isVisible():
                offset.setY(offset.y() + rect.height())
                block = block.next()
                continue

            for cursor in cursor_list:
                cursor_pos = cursor.position()
                cursor_paint_pos = cursor_pos
                if cursor_paint_pos < -1:
                    cursor_paint_pos = layout.preeditAreaPosition() - (cursor_paint_pos + 2)

                else:
                    cursor_paint_pos -= block_position

                draw_cursor = cursor_is_visible and text_editable and block_position <= cursor_pos < block_position + block_size
                if draw_cursor:
                    layout.drawCursor(painter, offset, cursor_paint_pos, cursor_width)
                    need_update_viewport = True

            offset.setY(offset.y() + rect.height())
            if offset.y() > viewport_rect.height():
                break

            block = block.next()

        if need_update_viewport:
            viewport.update()  # force update viewport with additional cursors

    def focusInEvent(self, e):
        if self._highlighter.completer():
            self._highlighter.completer().setWidget(self)

        super(BaseEditor, self).focusInEvent(e)

    def set_auto_hightlight_selection(self, enabled):
        self._auto_hightlight_selection = enabled

    def auto_hightlight_selection(self):
        return self._auto_hightlight_selection

    def set_auto_hightlight_focus(self, enabled):
        self._auto_hightlight_focus = enabled

    def auto_hightlight_focus(self):
        return self._auto_hightlight_focus

    def set_auto_hightlight_ignore_case(self, enabled):
        self._auto_hightlight_ignore_case = enabled

    def auto_hightlight_ignore_case(self):
        return self._auto_hightlight_ignore_case

    def set_auto_indentation(self, enabled):
        self._auto_indentation = enabled

    def auto_indentation(self):
        return self._auto_indentation

    def set_auto_parentheses(self, enabled):
        self._auto_parentheses = enabled

    def auto_parentheses(self):
        return self._auto_parentheses

    def set_tab_auto_replace(self, enabled):
        self._replace_tab = enabled

    def tab_auto_replace(self):
        return self._replace_tab

    def set_tab_size(self, val):
        self._replace_tab_by = ' ' * val
        metrics = self.fontMetrics()
        if QT_VERSION >= (5, 0, 0):
            self.setTabStopDistance(val * metrics.width(' '))

        else:
            self.setTabStopWidth(val * metrics.width(' '))

    def tab_size(self):
        return len(self._replace_tab_by)

    def insert_completion(self, s):
        if self._highlighter.completer().widget() != self:
            return

        tc = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        tc.insertText(s)
        self.setTextCursor(tc)

    def completer(self):
        return self._highlighter.completer()

    def char_under_cursor(self, cursor, offset=0):
        block = cursor.blockNumber()
        index = cursor.positionInBlock()
        text = self.document().findBlockByNumber(block).text()

        index += offset

        if index < 0 or index >= len(text):
            return []

        return text[index]

    def word_under_cursor(self, cursor):
        cursor.select(QTextCursor.WordUnderCursor)
        return cursor.selectedText()

    def insertFromMimeData(self, source):
        cursor_list = self.get_text_cursors()
        for cursor in cursor_list:
            cursor.insertText(source.text())

    def get_default_indent(self):
        if QT_VERSION >= (5, 0, 0):
            default_indent = int(self.tabStopDistance() / self.fontMetrics().averageCharWidth())

        else:
            default_indent = int(self.tabStopWidth() / self.fontMetrics().averageCharWidth())

        return default_indent

    def get_current_indent(self, cursor, as_tabs=False):
        block_text = cursor.block().text()
        indent = self.get_indent_from_string(block_text)

        if as_tabs:
            if QT_VERSION >= (5, 0, 0):
                indent = indent * int(self.fontMetrics().averageCharWidth() / self.tabStopDistance())

            else:
                indent = indent * int(self.fontMetrics().averageCharWidth() / self.tabStopWidth())

        return indent

    def get_indent_from_string(self, text):
        tab_spaces = int(self.tabStopWidth() / self.fontMetrics().averageCharWidth())
        line_spaces = []
        lines = text.splitlines()
        lines = lines if lines else [text]
        for line in lines:
            line_spaces.append(0)
            for ch in line:
                if ch == '\t':
                    line_spaces[-1] += tab_spaces

                elif ch == ' ':
                    line_spaces[-1] += 1

                else:
                    break

        result = min(line_spaces)
        return result
