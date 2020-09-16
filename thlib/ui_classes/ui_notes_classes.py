# file ui_notes_classes.py
# Notes panel

import thlib.side.six as six
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

from thlib.environment import env_server, env_inst, env_read_config, env_write_config
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
        self.task_widget_expanded = False
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

    def clear_notes(self):

        for i in range(self.main_notes_layout.count()):
            item = self.main_notes_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.close()

        if self.notes_widget:
            self.notes_widget.close()
            self.notes_widget = None

        if self.task_widget:
            self.task_widget.close()
            self.task_widget = None

    def show_notes(self, sobject, context='publish'):
        self.sobject = sobject
        self.context = context

        self.query_tasks_and_notes()

        self.bring_dock_widget_up()

    def set_sobject(self, sobject, context='publish'):
        self.sobject = sobject
        self.context = context

        if not self.visibleRegion().isEmpty():

            self.query_tasks_and_notes()

    def fill_tasks_and_notes(self, query_result):

        tasks, notes = query_result

        self.clear_notes()

        self.toggle_no_notes_label()

        self.task_widget = Ui_taskWidget(process=self.context, parent_sobject=self.sobject, type='extended', parent=self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.task_widget.setSizePolicy(sizePolicy)
        self.task_widget.setMaximumHeight(170)
        self.main_notes_layout.addWidget(self.task_widget)
        self.task_widget.expanded = self.task_widget_expanded

        self.notes_widget = Ui_notesWidget(sobject=self.sobject, context=self.context, task_widget=self.task_widget, parent=self)
        self.main_notes_layout.addWidget(self.notes_widget)
        self.notes_widget.show()

        self.main_notes_layout.setStretch(0, 0)
        self.main_notes_layout.setStretch(1, 1)

        self.task_widget.refresh_tasks_sobjects((tasks, None))
        self.notes_widget.fill_notes((notes, None))

    def query_tasks_and_notes(self):

        worker = env_inst.server_pool.add_task(tc.get_tasks_and_notes, sobject=self.sobject, process=self.context)
        worker.result.connect(self.fill_tasks_and_notes)
        worker.error.connect(gf.error_handle)
        worker.start()

    def set_settings_from_dict(self, settings_dict=None):
        if settings_dict:
            self.task_widget_expanded = settings_dict['task_expanded']

    def get_settings_dict(self):
        settings_dict = dict()
        settings_dict['task_expanded'] = self.task_widget_expanded

        return settings_dict

    def readSettings(self):

        self.set_settings_from_dict(env_read_config(filename='ui_notes', unique_id='ui_main', long_abs_path=True))

    def writeSettings(self):

        env_write_config(self.get_settings_dict(), filename='ui_notes', unique_id='ui_main', long_abs_path=True)

    def hideEvent(self, event):
        self.writeSettings()
        event.accept()


class Ui_notesWidget(QtGui.QWidget):
    def __init__(self, sobject=None, context=None, task_widget=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui_raw()

        self.sobject = sobject
        self.context = context

        self.task_widget = task_widget

        self.controls_actions()

    def create_ui_raw(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.conversationScrollArea = QtGui.QScrollArea()
        # self.conversationScrollArea.setWidgetResizable(True)
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
        self.reply_text_edit.setFixedHeight(32)

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

    def query_notes(self):

        worker = env_inst.server_pool.add_task(self.sobject.get_notes_sobjects, self.context)
        worker.result.connect(self.fill_notes)
        worker.error.connect(gf.error_handle)
        worker.start()

    def fill_notes(self, query_result):

        self.notes_sobjects, info = query_result

        notes_sobjects = list(self.notes_sobjects.values())

        self.create_scroll_area()
        self.current_user = env_server.get_user()
        self.widgets_list = []

        task_status_log = []
        current_task_sobject = None
        if self.task_widget:
            current_task_sobject = self.task_widget.get_current_task_sobject()
            if current_task_sobject:
                task_status_log = current_task_sobject.get_status_log()

        status_and_notes = task_status_log + notes_sobjects

        status_and_notes_sorted = tc.group_sobject_by(status_and_notes, 'timestamp')

        for date, sobject in status_and_notes_sorted:
            # almost not possible to have same timestamp, so skip checking
            sobject = sobject[0]

            if sobject.info['login'] == self.current_user:
                message_type = 'out'
            else:
                message_type = 'in'

            if sobject.get_plain_search_type() == 'sthpw/note':
                note_widget = Ui_messageWidget(sobject, message_type, self.sobject, current_task_sobject, self)
                self.lay.addWidget(note_widget)
                self.widgets_list.append(note_widget)
            else:
                status_widget = Ui_statusWidget(sobject, message_type, self.sobject, current_task_sobject, self)
                self.lay.addWidget(status_widget)
                self.widgets_list.append(status_widget)

        if self.widgets_list:
            QtGui.QApplication.processEvents()
            self.conversationScrollArea.setWidgetResizable(True)
            self.conversationScrollArea.ensureWidgetVisible(self.widgets_list[-1])

    def reply_note(self):

        search_type = self.sobject.info['__search_key__']
        process = self.context
        context = process
        login = self.current_user

        note = self.reply_text_edit.toPlainText()
        self.reply_text_edit.clear()

        if note:
            if not note.startswith(' '):
                new_note = tc.add_note(search_type, process, context, note, login)
                self.query_notes()
        else:
            self.reply_text_edit.setPlainText(None)

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()


class Ui_messageWidget(QtGui.QWidget):
    def __init__(self, note, message_type='out', parent_sobject=None, task_sobject=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.note = note
        self.parent_sobject = parent_sobject
        self.task_sobject = task_sobject
        self.login = env_inst.get_all_logins(self.note.info['login'])
        self.message_type = message_type
        self.attachment_size = 0

        self.create_ui_raw()

        self.customize_ui()

        self.initial_fill()

        self.controls_actions()

    def create_ui_raw(self):

        self.setObjectName('messageWidget')
        self.setMinimumWidth(260)
        self.setMinimumHeight(40)

        self.main_layout = QtGui.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.message_layout = QtGui.QVBoxLayout()
        self.message_layout.setContentsMargins(0, 0, 0, 0)
        self.message_layout.setSpacing(0)

        # self.attachments_layout = QtGui.QHBoxLayout()

        from thlib.side.flowlayout import FlowLayout
        # self.scroll_area.setWidgetResizable(True)
        # self.scroll_area.setFrameShape(QtGui.QFrame.NoFrame)
        # self.scroll_area.setWidget(self.scroll_area_contents)

        self.attachments_layout = FlowLayout()

        self.attachments_layout.setAlignment(QtCore.Qt.AlignTop)

        # self.attachments_layout = QtGui.QHBoxLayout()
        self.attachments_layout.setContentsMargins(0, 0, 0, 20)
        self.attachments_layout.setSpacing(0)

        self.message_frame = QtGui.QFrame()
        self.message_frame.setLayout(self.message_layout)

        self.text_area = QtGui.QTextBrowser()
        self.text_area.setMinimumWidth(40)
        self.text_area.setOpenExternalLinks(True)
        self.text_area.setFrameShape(QtGui.QFrame.NoFrame)
        self.text_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.text_area.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByKeyboard | QtCore.Qt.TextSelectableByMouse | QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.LinksAccessibleByKeyboard)

        self.message_layout.addWidget(self.text_area)
        self.message_layout.addLayout(self.attachments_layout)

        self.user_icon_widget = Ui_userIconWidget(self.login)

        self.user_icon_layout = QtGui.QVBoxLayout()
        self.user_icon_layout.setContentsMargins(0, 0, 0, 0)
        self.user_icon_layout.setSpacing(0)
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.user_icon_layout.addItem(spacerItem)
        self.user_icon_layout.addWidget(self.user_icon_widget)

        if self.message_type == 'in':
            self.main_layout.addLayout(self.user_icon_layout)
            self.main_layout.addWidget(self.message_frame)
            spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
            self.main_layout.addItem(spacerItem)

            self.main_layout.setStretch(0, 0)
            self.main_layout.setStretch(1, 0)
            self.main_layout.setStretch(2, 1)

        if self.message_type == 'out':
            spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
            self.main_layout.addItem(spacerItem)
            self.main_layout.addWidget(self.message_frame)
            self.main_layout.addLayout(self.user_icon_layout)
            self.main_layout.setStretch(0, 1)
            self.main_layout.setStretch(1, 0)
            self.main_layout.setStretch(2, 0)

        self.overlay_widget = QtGui.QWidget(self.message_frame)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.overlay_widget.setSizePolicy(sizePolicy)

        self.overlay_layout = QtGui.QGridLayout(self.overlay_widget)
        self.overlay_layout.setSpacing(0)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)

        self.overlay_widget.setLayout(self.overlay_layout)

        self.user_label = QtGui.QLabel()
        self.user_label.setStyleSheet('QLabel {padding-left: 8px; font-size: 10pt; color: grey;}')

        self.overlay_layout.addWidget(self.user_label, 0, 0, 1, 1)
        self.message_options_button = StyledToolButton(size='small')
        self.message_options_button.setParent(self.message_frame)
        self.message_options_button.setIcon(gf.get_icon('dots-vertical', icons_set='mdi', scale_factor=1.2))
        self.overlay_layout.addWidget(self.message_options_button, 0, 1, 1, 1)
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

    def controls_actions(self):

        self.message_options_button.clicked.connect(self.open_task_menu)

    def customize_ui(self):
        if self.message_type == 'out':
            customize_dict = {'bottom_left_radius': 6, 'bottom_right_radius': 0}
        else:
            customize_dict = {'bottom_left_radius': 0, 'bottom_right_radius': 6}

        # it is hacky, because it making frames around all objects

        self.message_frame.setStyleSheet("""
        QFrame {{
            border: 0px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            border-bottom-right-radius: {bottom_right_radius}px;
            border-bottom-left-radius: {bottom_left_radius}px;
            background: rgb(64, 64, 64);
            selection-background-color: darkgray;
        }}""".format(**customize_dict))

        self.text_area.setStyleSheet("""
        QTextEdit, QListView {
            font-size: 11pt;
            border: 0px;
            show-decoration-selected: 0;
            background: rgb(64, 64, 64);
            selection-background-color: darkgray;
            padding-top: 32px;
            padding-right: 8px;
            padding-left: 8px;
            padding-bottom: 0px;
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

    def initial_fill(self):
        note_text = self.note.info['note']

        if note_text:
            if isinstance(note_text, six.string_types):

                links_highlighted_text = gf.sub_urls(note_text)

                note_text = links_highlighted_text.replace('\n', '<br>')

                self.text_area.setHtml(note_text)
            else:
                links_highlighted_text = gf.sub_urls(note_text.decode('utf-8'))

                note_text = links_highlighted_text.replace('\n', '<br>')

                self.text_area.setHtml(note_text)

        attachment = self.note.get_process('reference/attachment')
        if attachment:
            contexts = attachment.get_contexts()

            snapshots = []
            for context in contexts.values():
                snapshots.extend(context.get_versions().values())

            for snapshot in snapshots:
                # print(snapshot.get_files_objects())
                # print(snapshot.get_previewable_files_objects())
                # self.message_layout.addWidget(QtGui.QPushButton('asd'))

                preview_files_objects = snapshot.get_previewable_files_objects()

                if not preview_files_objects:
                    # Trying to gen any preview if possible
                    for fo in snapshot.get_files_objects():
                        if fo.get_type() == 'web':
                            if fo not in preview_files_objects:
                                preview_files_objects.append(fo)

                if preview_files_objects:
                    file_object = preview_files_objects[0]

                    repo_sync_item = env_inst.ui_repo_sync_queue.schedule_file_object(file_object)
                    # repo_sync_item.downloaded.connect(self.set_preview_pixmap)
                    repo_sync_item.download()

                    pixmap = Qt4Gui.QPixmap(file_object.get_full_abs_path())

                    pic_label = QtGui.QLabel()
                    pic_label.setStyleSheet(
                        "QLabel {background: rgba(175, 175, 175, 16); border: 0px; border-radius: 3px; padding: 0px 0px; }")
                    pic_label.setAlignment(QtCore.Qt.AlignCenter)

                    if pixmap.height() > pixmap.width():
                        pic_label.setPixmap(pixmap.scaledToWidth(64, QtCore.Qt.SmoothTransformation))
                    else:
                        pic_label.setPixmap(pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation))

                    pic_label.setMinimumSize(64, 64)
                    pic_label.setMaximumSize(64, 64)

                    self.attachments_layout.addWidget(pic_label)
                    self.attachment_size += 64

        self.text_area.setLineWrapColumnOrWidth(self.width())

        text_document = self.text_area.document()
        document_size = text_document.size()
        doc_height = document_size.height() + 10
        self.setMinimumHeight(doc_height)

        self.text_area.setLineWrapMode(QtGui.QTextEdit.FixedPixelWidth)

        self.text_area.setCursorWidth(0)

        # TODO Add login info, like group etc
        if self.login:
            self.user_label.setText(u'{0} ({1})'.format(self.login.get_display_name(), self.login.get_value('login')))
            self.user_label.setStyleSheet('QLabel {{padding-left: 8px; font-size: 10pt; color: {0};}}'.format(gf.gen_color(self.login.get_value('login'))))
        else:
            self.user_label.setText(u'{0} (removed user)'.format(self.note.get_value('login')))

        self.date_label.setText(self.note.get_timestamp(pretty=True))

    def open_task_menu(self):
        menu = self.note_options_menu()
        if menu:
            menu.exec_(Qt4Gui.QCursor.pos())

    def edit_message(self):
        print('Editing message')

    def delete_message(self):
        self.note.delete_sobject()
        self.setHidden(True)

    def note_options_menu(self):

        # add_task = QtGui.QAction('Change Status', self.tasks_options_button)
        # add_task.setIcon(gf.get_icon('plus', icons_set='mdi', scale_factor=1))
        # add_task.triggered.connect(self.add_new_task)

        edit_message = QtGui.QAction('Edit', self.message_options_button)
        edit_message.setIcon(gf.get_icon('square-edit-outline', icons_set='mdi', scale_factor=1))
        edit_message.triggered.connect(self.edit_message)

        delete_message = QtGui.QAction('Delete', self.message_options_button)
        delete_message.setIcon(gf.get_icon('delete-forever', icons_set='mdi', scale_factor=1))
        delete_message.triggered.connect(self.delete_message)

        # enable_watch = QtGui.QAction('Enable Watch', self.tasks_options_button)
        # enable_watch.setIcon(gf.get_icon('eye'))
        #
        # disable_watch = QtGui.QAction('Disable Watch', self.tasks_options_button)
        # disable_watch.setIcon(gf.get_icon('eye-slash'))

        menu = QtGui.QMenu()

        menu.addAction(edit_message)
        menu.addAction(delete_message)

        # if self.tasks_sobjects_list:
        #
        #     menu.addAction(edit_task)
        #     menu.addAction(delete_task)
        #     menu.addSeparator()
        #
        #     for task_sobject in self.tasks_sobjects_list:
        #         task_action = QtGui.QAction(u'Task: {0} / {1}'.format(
        #             task_sobject.get_value('context'),
        #             task_sobject.get_value('assigned')
        #         ), self.tasks_options_button)
        #
        #         task_action.setCheckable(True)
        #
        #         if task_sobject == self.current_task_sobject:
        #             task_action.setChecked(True)
        #         elif task_sobject.get_value('login') == env_inst.get_current_login():
        #             task_action.setChecked(True)
        #
        #         task_action.triggered.connect(partial(self.customize_by_task_sobject, task_sobject))
        #
        #         menu.addAction(task_action)

        return menu

    def resizeEvent(self, event):
        event.accept()

        self.text_area.setLineWrapColumnOrWidth(self.width() - 80)
        text_document = self.text_area.document()
        metrics = Qt4Gui.QFontMetrics(self.text_area.font())

        document_size = text_document.size()

        doc_height = document_size.height() + 64

        self.text_area.setFixedHeight(doc_height-30)

        doc_width = document_size.width()
        text_rect = metrics.boundingRect(QtCore.QRect(), 0, self.text_area.toPlainText())
        login_rect = metrics.boundingRect(QtCore.QRect(), 0, self.user_label.text())
        text_width = text_rect.width() + login_rect.width() + 20

        if text_width < doc_width:
            self.message_frame.setFixedWidth(text_width)
        else:
            self.message_frame.setFixedWidth(doc_width + 20)

        if self.message_type == 'out':
            x_pos = self.width() - (self.message_frame.width() + 60)

            self.message_frame.move(x_pos, 0)
        else:
            self.message_frame.move(60, 0)

        text_area_size = self.message_frame.size()

        self.overlay_widget.resize(text_area_size)

        overlay_reg = Qt4Gui.QRegion(self.overlay_widget.frameGeometry())
        text_area_reg = Qt4Gui.QRegion(QtCore.QRect(0, 36, text_area_size.width(), text_area_size.height()-60))

        self.overlay_widget.setMask(overlay_reg.subtracted(text_area_reg))

        # self.setMinimumHeight(doc_height)
        if self.attachment_size > 0:
            self.setFixedHeight(doc_height + 74)
        else:
            self.setFixedHeight(doc_height)


class Ui_statusWidget(QtGui.QWidget):
    def __init__(self, status, message_type='out', parent_sobject=None, task_sobject=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.status = status
        self.parent_sobject = parent_sobject
        self.task_sobject = task_sobject
        self.login = env_inst.get_all_logins(self.status.info['login'])
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
        corner = QtGui.QWidget()
        corner.setFixedSize(34, 34)
        self.overlay_layout.addWidget(corner, 0, 1, 1, 1)
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
        self.date_label.setText(self.status.get_timestamp(simple=True))
        event.accept()

    def date_label_leave_event(self, event):
        self.date_label.setText(self.status.get_timestamp(pretty=True))
        event.accept()

    def get_status_color(self):

        stype = self.parent_sobject.get_stype()

        workflow = stype.get_workflow()
        tasks_pipelines = workflow.get_by_stype_code('sthpw/task')

        status_color = '#ffffff'

        task_pipeline_code = self.task_sobject.info.get('pipeline_code')
        status = self.status.get_value('to_status')

        if task_pipeline_code:
            task_pipeline = tasks_pipelines.get(task_pipeline_code)
            status_info = task_pipeline.get_pipeline_process(status)
            if status_info:
                status_color = status_info['color']

        item_color = gf.hex_to_rgb(status_color, alpha=48)

        return item_color

    def customize_ui(self):
        if self.message_type == 'out':
            customize_dict = {'bottom_left_radius': 6, 'bottom_right_radius': 0}
        else:
            customize_dict = {'bottom_left_radius': 0, 'bottom_right_radius': 6}

        customize_dict['status_color'] = self.get_status_color()

        self.text_area.setStyleSheet("""
        QTextEdit, QListView {{
            font-size: 11pt;
            border: 0px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            border-bottom-right-radius: {bottom_right_radius}px;
            border-bottom-left-radius: {bottom_left_radius}px;
            show-decoration-selected: 0;
            background: {status_color};
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
        status_text = u'{0}'.format(self.status.get_value('to_status'))

        self.text_area.setHtml(status_text)

        self.text_area.setLineWrapColumnOrWidth(self.width())

        text_document = self.text_area.document()
        document_size = text_document.size()
        doc_height = document_size.height() + 10
        self.setMinimumHeight(doc_height)

        self.text_area.setLineWrapMode(QtGui.QTextEdit.FixedPixelWidth)

        self.text_area.setCursorWidth(0)

        # TODO Add login info, like group etc
        self.user_label.setText(u'{0} ({1})'.format(self.login.get_display_name(), self.login.get_value('login')))
        self.user_label.setStyleSheet('QLabel {{padding-left: 8px; font-size: 10pt; color: {0};}}'.format(gf.gen_color(self.login.get_value('login'))))

        self.date_label.setText(self.status.get_timestamp(pretty=True))

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
