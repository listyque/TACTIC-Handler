# file ui_notes_classes.py
# Notes panel

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

from thlib.environment import env_server, env_inst
from thlib.ui_classes.ui_custom_qwidgets import StyledToolButton, Ui_userIconWidget
from thlib.ui_classes.ui_tasks_classes import Ui_taskWidget
import thlib.tactic_classes as tc
import thlib.global_functions as gf


class Ui_notesBaseWidget(QtGui.QWidget):
    def __init__(self, project=None, sobject=None, context=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project
        self.sobject = sobject
        self.context = context
        self.notes_widget = None
        self.task_widget = None
        self.sobjects_list = []

        self.create_ui()

        # self.controls_actions()

    def controls_actions(self):

        self.notes_tab_widget.tabCloseRequested.connect(self.close_notes_tab)

    def create_ui(self):

        self.create_no_notes_label()

        self.main_notes_layout = QtGui.QVBoxLayout()
        self.main_notes_layout.setSpacing(0)
        self.main_notes_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_notes_layout)

        self.main_notes_layout.addWidget(self.no_notes_label)

    def create_no_notes_label(self):
        self.no_notes_label = QtGui.QLabel()
        self.no_notes_label.setText('No Notes...')
        self.no_notes_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

    def toggle_no_notes_label(self):
        if self.notes_widget:
            self.no_notes_label.setHidden(False)
            self.notes_widget.setHidden(True)
        else:
            self.no_notes_label.setHidden(True)

    def bring_dock_widget_up(self):

        related_notes_dock = env_inst.get_check_tree(
            self.project.get_code(), 'checkin_out_instanced_widgets', 'notes_dock')

        dock_widget = related_notes_dock.parent()
        if dock_widget:
            if isinstance(dock_widget, QtGui.QDockWidget):
                dock_widget.setHidden(False)
                dock_widget.raise_()

    def show_notes(self, sobject, context):
        if self.notes_widget:
            self.notes_widget.close()
            self.notes_widget = None

        if self.task_widget:
            self.task_widget.close()
            self.task_widget = None

        self.toggle_no_notes_label()

        self.task_widget = Ui_taskWidget(process=context, parent_sobject=sobject, type='extended', parent=self)
        self.task_widget.refresh_tasks_sobjects()

        self.main_notes_layout.addWidget(self.task_widget)

        self.notes_widget = Ui_notesWidget(sobject=sobject, context=context, parent=self)

        self.main_notes_layout.addWidget(self.notes_widget)

        self.notes_widget.fill_notes()

        self.bring_dock_widget_up()


class Ui_notesWidget(QtGui.QWidget):
    def __init__(self, sobject=None, context=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui_raw()

        self.sobject = sobject
        self.context = context

        self.controls_actions()

    def create_ui_raw(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.conversationScrollArea = QtGui.QScrollArea()
        self.conversationScrollArea.setWidgetResizable(True)
        self.conversationScrollArea.setFrameShape(QtGui.QFrame.NoFrame)

        self.conversationScrollArea.setStyleSheet("""
        QScrollArea {
            background: rgb(52, 52, 52);
        }
        QScrollArea > QWidget > QWidget {
            background: rgb(52, 52, 52);
        }
        QScrollBar:vertical {
            border: 0px ;
            background: transparent;
            width:8px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: rgba(255,255,255,64);
            min-height: 0px;
            border-radius: 4px;
        }
        QScrollBar::add-line:vertical {
            background: rgba(255,255,255,64);
            height: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }
        QScrollBar::sub-line:vertical {
            background: rgba(255,255,255,64);
            height: 0 px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }
        QScrollBar:horizontal {
            border: 0px ;
            background: transparent;
            height:8px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:horizontal {
            background: rgba(255,255,255,64);
            min-height: 0px;
            border-radius: 4px;
        }
        QScrollBar::add-line:horizontal {
            background: rgba(255,255,255,64);
            height: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }
        QScrollBar::sub-line:horizontal {
            background: rgba(255,255,255,64);
            height: 0 px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }""")

        self.main_layout.addWidget(self.conversationScrollArea)

        self.editor_layout = QtGui.QHBoxLayout()
        self.editor_layout.setContentsMargins(0, 4, 0, 4)
        self.editor_layout.setSpacing(0)

        self.attachment_tool_button = StyledToolButton()
        self.attachment_tool_button.setIcon(gf.get_icon('paperclip', icons_set='mdi', scale_factor=1.2))
        self.editor_layout.addWidget(self.attachment_tool_button)

        self.reply_text_edit = QtGui.QPlainTextEdit()
        self.reply_text_edit.setFrameShape(QtGui.QFrame.NoFrame)
        self.reply_text_edit.setStyleSheet("""
        QPlainTextEdit, QListView {
            font-size:11pt;
            border: 0px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
            border-bottom-left-radius: 4px;
            show-decoration-selected: 1;
            background: rgb(43, 43, 43);
            selection-background-color: darkgray;
            padding-top: 2px;
            padding-right: 4px;
            padding-left: 4px;
        }
        QScrollBar:vertical {
            border: 0px ;
            background: transparent;
            width:8px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: rgba(255,255,255,64);
            min-height: 0px;
            border-radius: 4px;
        }
        QScrollBar::add-line:vertical {
            background: rgba(255,255,255,64);
            height: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }
        QScrollBar::sub-line:vertical {
            background: rgba(255,255,255,64);
            height: 0 px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }""")
        self.reply_text_edit.setMaximumHeight(32)
        self.reply_text_edit.setMinimumHeight(32)

        self.editor_layout.addWidget(self.reply_text_edit)

        self.reply_tool_button = StyledToolButton()
        self.reply_tool_button.setIcon(gf.get_icon('send', icons_set='mdi', scale_factor=1.2))
        self.editor_layout.addWidget(self.reply_tool_button)

        self.main_layout.addLayout(self.editor_layout, 1, 0)

        self.main_layout.setRowStretch(0, 1)

    def controls_actions(self):
        self.reply_tool_button.clicked.connect(self.reply_note)
        self.reply_text_edit.textChanged.connect(self.reply_text_edit_text_changed)

    def create_scroll_area(self):
        self.scrollAreaContents = QtGui.QWidget()
        self.lay = QtGui.QVBoxLayout(self.scrollAreaContents)
        self.lay.setAlignment(QtCore.Qt.AlignBottom)
        self.conversationScrollArea.setWidget(self.scrollAreaContents)
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.lay.addItem(spacerItem)
        self.lay.setStretch(0, 1)

    def reply_text_edit_text_changed(self):

        text_document = self.reply_text_edit.document()

        if text_document.lineCount() > 1:
            doc_height = 32 + 19 * text_document.lineCount()
            self.reply_text_edit.setMinimumHeight(doc_height)
            self.reply_text_edit.setMaximumHeight(doc_height)
        else:
            self.reply_text_edit.setMinimumHeight(32)
            self.reply_text_edit.setMaximumHeight(32)

    def fill_notes(self):

        self.create_scroll_area()
        self.current_user = env_server.get_user()
        self.sobject.get_notes()
        self.widgets_list = []

        for proc in self.sobject.notes.values():
            for context in proc.contexts.values():
                for note in reversed(list(context.items.values())):
                    if note.info['context'] == self.context:
                        if note.info['login'] == self.current_user:
                            self.note_widget = Ui_messageWidget(note, 'out', self)
                            self.lay.addWidget(self.note_widget)
                            self.widgets_list.append(self.note_widget)
                        else:
                            self.note_widget = Ui_messageWidget(note, 'in', self)
                            self.lay.addWidget(self.note_widget)
                            self.widgets_list.append(self.note_widget)

        scroll_max = 0
        for w in self.widgets_list:
            scroll_max += w.height()

        self.conversationScrollArea.verticalScrollBar().setValue(scroll_max)

    def reply_note(self):

        search_type = self.sobject.info['__search_key__']
        process = self.context
        context = process
        note = self.reply_text_edit.toPlainText()
        login = self.current_user

        new_note = tc.add_note(search_type, process, context, note, login)
        self.fill_notes()

        self.reply_text_edit.clear()

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()


class Ui_messageWidget(QtGui.QWidget):
    def __init__(self, note, message_type='out', parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.note = note
        self.login = env_inst.get_all_logins(self.note.info['login'])
        self.message_type = message_type

        self.create_ui_raw()

        self.customize_ui()

        self.initial_fill()

    def create_ui_raw(self):

        self.setMinimumWidth(260)
        self.setMinimumHeight(40)

        self.main_layout = QtGui.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.text_area = QtGui.QTextBrowser()
        self.text_area.setMinimumWidth(40)
        self.text_area.setOpenExternalLinks(True)
        self.text_area.setFrameShape(QtGui.QFrame.NoFrame)
        self.text_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.text_area.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByKeyboard | QtCore.Qt.TextSelectableByMouse | QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.LinksAccessibleByKeyboard)

        self.user_icon_widget = Ui_userIconWidget(self.login)

        self.user_icon_layout = QtGui.QVBoxLayout()
        self.user_icon_layout.setContentsMargins(0, 0, 0, 0)
        self.user_icon_layout.setSpacing(0)
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.user_icon_layout.addItem(spacerItem)
        self.user_icon_layout.addWidget(self.user_icon_widget)

        if self.message_type == 'in':
            self.main_layout.addLayout(self.user_icon_layout)
            self.main_layout.addWidget(self.text_area)
            spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
            self.main_layout.addItem(spacerItem)

            self.main_layout.setStretch(0, 0)
            self.main_layout.setStretch(1, 0)
            self.main_layout.setStretch(2, 1)

        if self.message_type == 'out':
            spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
            self.main_layout.addItem(spacerItem)
            self.main_layout.addWidget(self.text_area)
            self.main_layout.addLayout(self.user_icon_layout)
            self.main_layout.setStretch(0, 1)
            self.main_layout.setStretch(1, 0)
            self.main_layout.setStretch(2, 0)

        self.overlay_widget = QtGui.QWidget(self.text_area)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.overlay_widget.setSizePolicy(sizePolicy)

        self.overlay_layout = QtGui.QGridLayout(self.overlay_widget)
        self.overlay_layout.setSpacing(0)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)

        self.overlay_widget.setLayout(self.overlay_layout)

        self.user_label = QtGui.QLabel()
        self.user_label.setStyleSheet('QLabel {padding-left: 8px; font-size: 10pt; color: grey;}')

        self.overlay_layout.addWidget(self.user_label, 0, 0, 1, 1)
        self.toolButton = StyledToolButton(small=True)
        self.toolButton.setParent(self.text_area)
        self.toolButton.setIcon(gf.get_icon('dots-vertical', icons_set='mdi', scale_factor=1.2))
        self.overlay_layout.addWidget(self.toolButton, 0, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.overlay_layout.addItem(spacerItem, 1, 0, 1, 2)

        self.date_label = QtGui.QLabel()
        self.date_label.enterEvent = self.date_label_enter_event
        self.date_label.leaveEvent = self.date_label_leave_event
        self.date_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.date_label.setStyleSheet('QLabel {padding-right: 8px; padding-bottom: 8px; font-size: 10pt; color: grey;}')
        self.overlay_layout.addWidget(self.date_label, 2, 0, 1, 2)

        self.overlay_widget.raise_()

    def date_label_enter_event(self, event):
        self.date_label.setText(self.note.get_timestamp(simple=True))
        event.accept()

    def date_label_leave_event(self, event):
        self.date_label.setText(self.note.get_timestamp(pretty=True))
        event.accept()

    def customize_ui(self):
        if self.message_type == 'out':
            customize_dict = {'bottom_left_radius': 6, 'bottom_right_radius': 0}
        else:
            customize_dict = {'bottom_left_radius': 0, 'bottom_right_radius': 6}

        self.text_area.setStyleSheet("""
        QTextEdit, QListView {{
            font-size: 11pt;
            border: 0px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            border-bottom-right-radius: {bottom_right_radius}px;
            border-bottom-left-radius: {bottom_left_radius}px;
            show-decoration-selected: 0;
            background: rgb(64, 64, 64);
            selection-background-color: darkgray;
            padding-top: 32px;
            padding-right: 8px;
            padding-left: 8px;
            padding-bottom: 26px;
        }}
        QScrollBar:vertical {{
            border: 0px ;
            background: transparent;
            width:8px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255,255,255,64);
            min-height: 0px;
            border-radius: 4px;
        }}
        QScrollBar::add-line:vertical {{
            background: rgba(255,255,255,64);
            height: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }}
        QScrollBar::sub-line:vertical {{
            background: rgba(255,255,255,64);
            height: 0 px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }}""".format(**customize_dict))

    def initial_fill(self):
        note_text = self.note.info['note']

        if note_text:
            if isinstance(note_text, unicode):

                links_highlighted_text = gf.sub_urls(note_text)

                note_text = links_highlighted_text.replace('\n', '<br>')

                self.text_area.setHtml(note_text)
            else:
                links_highlighted_text = gf.sub_urls(note_text.decode('utf-8'))

                note_text = links_highlighted_text.replace('\n', '<br>')

                self.text_area.setHtml(note_text)

        self.text_area.setLineWrapColumnOrWidth(self.width())

        text_document = self.text_area.document()
        document_size = text_document.size()
        doc_height = document_size.height() + 10
        self.setMinimumHeight(doc_height)

        self.text_area.setLineWrapMode(QtGui.QTextEdit.FixedPixelWidth)

        self.text_area.setCursorWidth(0)

        # TODO Add login info, like group etc
        self.user_label.setText(u'{0} ({1})'.format(self.login.get_display_name(), self.login.get_value('login')))

        self.date_label.setText(self.note.get_timestamp(pretty=True))

    def resizeEvent(self, event):
        event.accept()

        self.text_area.setLineWrapColumnOrWidth(self.width() - 80)
        text_document = self.text_area.document()
        metrics = Qt4Gui.QFontMetrics(self.text_area.font())

        document_size = text_document.size()

        doc_height = document_size.height() + 64

        self.text_area.setFixedHeight(doc_height)

        doc_width = document_size.width()
        text_rect = metrics.boundingRect(QtCore.QRect(), 0, self.text_area.toPlainText())
        login_rect = metrics.boundingRect(QtCore.QRect(), 0, self.user_label.text())
        text_width = text_rect.width() + login_rect.width() + 20

        if text_width < doc_width:
            self.text_area.setFixedWidth(text_width)
        else:
            self.text_area.setFixedWidth(doc_width + 20)

        if self.message_type == 'out':
            x_pos = self.width() - (self.text_area.width() + 60)

            self.text_area.move(x_pos, 0)
        else:
            self.text_area.move(60, 0)

        text_area_size = self.text_area.size()

        self.overlay_widget.resize(text_area_size)

        overlay_reg = Qt4Gui.QRegion(self.overlay_widget.frameGeometry())
        text_area_reg = Qt4Gui.QRegion(QtCore.QRect(0, 36, text_area_size.width(), text_area_size.height()-60))

        self.overlay_widget.setMask(overlay_reg.subtracted(text_area_reg))

        self.setMinimumHeight(doc_height)
