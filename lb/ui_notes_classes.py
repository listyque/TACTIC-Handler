# file ui_notes_classes.py
# Notes panel

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import environment as env
import lib.ui.ui_notes as ui_notes
import ui_richedit_classes as richedit_widget
import lib.ui.ui_notes_incom as ui_incom
import lib.ui.ui_notes_outcom as ui_outcom
import tactic_classes as tc
import global_functions as gf

reload(ui_notes)
reload(ui_incom)
reload(ui_outcom)


class Ui_notesOwnWidget(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.statusBar()
        self.ui_notes = Ui_notesWidget(self)
        self.setCentralWidget(self.ui_notes)

    def closeEvent(self, event):
        print('Save Ui_notesOwnWidget')
        self.ui_notes.close()
        self.ui_notes.deleteLater()
        self.deleteLater()
        event.accept()


class Ui_notesWidget(QtGui.QWidget, ui_notes.Ui_notes):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.task_item = None

        self.ui_richedit = richedit_widget.Ui_richeditWidget(self.replyTextEdit, False)
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
        self.current_user = env.Env().get_user()
        self.task_item.get_notes()
        self.widgets_list = []
        for proc in self.task_item.notes.itervalues():
            for context in proc.contexts.itervalues():
                for note in reversed(list(context.items.itervalues())):
                    if note.info['process'] == self.task_item.info['process']:
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
        search_type = self.task_item.info['__search_key__']
        process = self.task_item.info['process']
        context = self.task_item.info['context']
        note = gf.simplify_html(self.replyTextEdit.toHtml())
        login = self.current_user

        tc.add_note(search_type, process, context, note, login)
        self.fill_notes()

    def closeEvent(self, event):
        print('Save Ui_notesWidget')
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
        self.commentLabel.setText(self.note.info['note'])
        self.dateLabel.setText(self.note.info['timestamp'])
        # print(self.note.info)

        # textBrowser->setHtml(noteContent.text);
        # textBrowser->setWordWrapMode(QTextOption::WrapAtWordBoundaryOrAnywhere);
        #
        # int textHeight;
        # textBrowser->document()->setTextWidth(width());
        # if (textBrowser->toPlainText().isEmpty())
        #     textHeight = 0;
        # else
        #     textHeight = textBrowser->document()->size().height() + 5;
        # textBrowser->setFixedHeight(textHeight);


class Ui_outcomWidget(QtGui.QWidget, ui_outcom.Ui_outcom):
    def __init__(self, note, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.note = note

        self.initial_fill()

    def initial_fill(self):
        self.authorLabel.setText(self.note.info['login'] + ':')
        self.commentLabel.setText(self.note.info['note'])
        self.dateLabel.setText(self.note.info['timestamp'])
