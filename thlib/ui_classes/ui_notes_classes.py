# file ui_notes_classes.py
# Notes panel

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore

from thlib.environment import env_server, env_inst
import thlib.ui.misc.ui_notes as ui_notes
import ui_richedit_classes as richedit_widget
import thlib.ui.items.ui_notes_incom as ui_incom
import thlib.ui.items.ui_notes_outcom as ui_outcom
import thlib.tactic_classes as tc
import thlib.global_functions as gf

reload(ui_notes)
reload(ui_incom)
reload(ui_outcom)


class Ui_notesTabbedWidget(QtGui.QWidget):
    def __init__(self, project=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project
        self.sobjects_list = []

        self.create_ui()
        self.controls_actions()

    def controls_actions(self):

        self.notes_tab_widget.tabCloseRequested.connect(self.close_notes_tab)

    def create_ui(self):

        self.create_no_notes_label()

        self.create_notes_tab_widget()

        self.main_notes_layout = QtGui.QVBoxLayout()
        self.main_notes_layout.setSpacing(0)
        self.main_notes_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_notes_layout)

        self.main_notes_layout.addWidget(self.no_notes_label)
        self.main_notes_layout.addWidget(self.notes_tab_widget)
        self.notes_tab_widget.setHidden(True)

    def create_no_notes_label(self):
        self.no_notes_label = QtGui.QLabel()
        self.no_notes_label.setText('No Notes...')
        self.no_notes_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        # self.no_notes_label.setMinimumWidth(200)

    def toggle_no_notes_label(self):
        if self.notes_tab_widget.count() == 0:
            self.no_notes_label.setHidden(False)
            self.notes_tab_widget.setHidden(True)
        else:
            self.notes_tab_widget.setHidden(False)
            self.no_notes_label.setHidden(True)

    def create_notes_tab_widget(self):
        self.notes_tab_widget = QtGui.QTabWidget()
        self.notes_tab_widget.setMovable(True)
        self.notes_tab_widget.setTabsClosable(True)
        self.notes_tab_widget.setObjectName("notes_tab_widget")
        self.notes_tab_widget.setStyleSheet(
            '#notes_tab_widget > QTabBar::tab {background: transparent;border: 2px solid transparent;'
            'border-top-left-radius: 3px;border-top-right-radius: 3px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;padding: 4px;}'
            '#notes_tab_widget > QTabBar::tab:selected, #notes_tab_widget > QTabBar::tab:hover {'
            'background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(255, 255, 255, 48), stop: 1 rgba(255, 255, 255, 32));}'
            '#notes_tab_widget > QTabBar::tab:selected {border-color: transparent;}'
            '#notes_tab_widget > QTabBar::tab:!selected {margin-top: 0px;}')

    def bring_dock_widget_up(self):

        related_notes_dock = env_inst.get_check_tree(
            self.project.get_code(), 'checkin_out_instanced_widgets', 'notes_dock')

        dock_widget = related_notes_dock.parent()
        if dock_widget:
            if isinstance(dock_widget, QtGui.QDockWidget):
                dock_widget.setHidden(False)
                dock_widget.raise_()

    def bring_tab_up(self, sobject, context):
        for i in range(self.notes_tab_widget.count()):
            note_widget = self.notes_tab_widget.widget(i)
            if (sobject.get_search_key(), context) == (note_widget.sobject.get_search_key(), note_widget.context):
                self.notes_tab_widget.setCurrentWidget(note_widget)

    def close_notes_tab(self, tab_index):
        note_widget = self.notes_tab_widget.widget(tab_index)
        self.sobjects_list.remove((note_widget.sobject.get_search_key(), note_widget.context))
        note_widget.close()
        self.notes_tab_widget.removeTab(tab_index)
        self.toggle_no_notes_label()

    def tab_is_unique(self, sobject, context):
        search_key = sobject.get_search_key()
        if (search_key, context) not in self.sobjects_list:
            self.sobjects_list.append((search_key, context))
            return sobject

    def add_notes_tab(self, sobject, context):
        if self.tab_is_unique(sobject, context):
            note_widget = Ui_notesWidget(self)

            tab_title = u'{0}/{1}'.format(sobject.get_title(), context)
            self.notes_tab_widget.addTab(note_widget, tab_title)

            note_widget.sobject = sobject
            note_widget.context = context

            note_widget.fill_notes()

            note_widget.conversationScrollArea.verticalScrollBar().setValue(
                note_widget.conversationScrollArea.verticalScrollBar().maximum())

            self.notes_tab_widget.setCurrentWidget(note_widget)
            self.toggle_no_notes_label()
        else:
            self.bring_tab_up(sobject, context)

        self.bring_dock_widget_up()


class Ui_notesWidget(QtGui.QWidget, ui_notes.Ui_notes):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.sobject = None
        self.context = None

        self.ui_richedit = richedit_widget.Ui_richeditWidget(self.replyTextEdit, True)
        self.editorLayout.addWidget(self.ui_richedit)

        self.controls_actions()

    def controls_actions(self):
        self.replyPushButton.clicked.connect(self.reply_note)

    def create_scroll_area(self):
        self.scrollAreaContents = QtGui.QWidget()
        self.lay = QtGui.QVBoxLayout(self.scrollAreaContents)
        self.lay.setAlignment(QtCore.Qt.AlignBottom)
        self.conversationScrollArea.setWidget(self.scrollAreaContents)

    def fill_notes(self):
        self.conversationScrollArea.close()
        self.create_scroll_area()
        self.current_user = env_server.get_user()
        self.sobject.get_notes()
        self.widgets_list = []
        for proc in self.sobject.notes.values():
            for context in proc.contexts.values():
                for note in reversed(list(context.items.values())):
                    if note.info['context'] == self.context:
                        if note.info['login'] == self.current_user:
                            self.note_widget = Ui_outcomWidget(note, self)
                            self.lay.addWidget(self.note_widget)
                            self.widgets_list.append(self.note_widget)
                        else:
                            self.note_widget = Ui_incomWidget(note, self)
                            self.lay.addWidget(self.note_widget)
                            self.widgets_list.append(self.note_widget)

        # looks like duct tape
        self.conversationScrollArea.show()

        # TODO make scroll_to_widget using line above
        # print(self.widgets_list[-1].height())
        self.conversationScrollArea.verticalScrollBar().setValue(
            self.conversationScrollArea.verticalScrollBar().maximum())

    def reply_note(self):
        search_type = self.sobject.info['__search_key__']
        process = self.context
        context = process
        note = self.replyTextEdit.toPlainText()
        note_html = self.replyTextEdit.toHtml()
        login = self.current_user

        tc.add_note(search_type, process, context, note, note_html, login)
        self.fill_notes()

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()


class Ui_incomWidget(QtGui.QWidget, ui_incom.Ui_incom):
    def __init__(self, note, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.note = note

        self.initial_fill()

    def initial_fill(self):

        self.authorLabel.setText(self.note.info['login'] + ':')
        if self.note.info.get('note_html'):
            note_text = gf.hex_to_html(self.note.info['note_html'])
            self.commentLabel.setTextFormat(QtCore.Qt.RichText)
        else:
            note_text = self.note.info['note']
            self.commentLabel.setTextFormat(QtCore.Qt.PlainText)
        self.commentLabel.setText(note_text)
        self.dateLabel.setText(self.note.info['timestamp'])


class Ui_outcomWidget(QtGui.QWidget, ui_outcom.Ui_outcom):
    def __init__(self, note, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.note = note

        self.initial_fill()

    def initial_fill(self):
        self.authorLabel.setText(self.note.info['login'] + ':')
        if self.note.info.get('note_html'):
            note_text = gf.hex_to_html(self.note.info['note_html'])
            self.commentLabel.setTextFormat(QtCore.Qt.RichText)
        else:
            note_text = self.note.info['note']
            self.commentLabel.setTextFormat(QtCore.Qt.PlainText)
        self.commentLabel.setText(note_text)
        self.dateLabel.setText(self.note.info['timestamp'])
