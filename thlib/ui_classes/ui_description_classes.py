from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

import thlib.tactic_classes as tc
import thlib.global_functions as gf
from thlib.ui.checkin_out.ui_description_widget import Ui_descriptionWidget
from thlib.ui_classes.ui_richedit_classes import Ui_richeditWidget


class Ui_descriptionWidget(QtGui.QWidget, Ui_descriptionWidget):
    def __init__(self, project, stype, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        self.project = project
        self.item = None
        self.descriptionTextEdit_freezed = False
        self.descriptionTextEdit_edited = False

        self.setupUi(self)

        self.create_ui()

    def create_ui(self):

        if self.stype:
            self.create_float_buttons()

        self.create_rich_edit()

        if self.stype:
            self.controls_actions()

    def controls_actions(self):
        self.descriptionTextEdit.cursorPositionChanged.connect(self.set_edit_mode)
        # self.descriptionTextEdit.textChanged.connect(self.set_edit_mode)
        # self.descriptionTextEdit.selectionChanged.connect(self.text_edit_select)
        self.clear_button.clicked.connect(self.unfreeze_text_edit)

        self.lock_button.clicked.connect(self.freeze_text_edit)

        self.edit_button.clicked.connect(self.set_edit_mode)
        self.save_button.clicked.connect(self.unset_edit_mode)
        self.save_button.clicked.connect(self.update_desctiption)

    def set_item(self, item):
        if not self.visibleRegion().isEmpty():
            self.item = item
            if self.item:
                self.customize_with_item()
            else:
                self.customize_without_item()

    def customize_with_item(self):

        if not self.descriptionTextEdit_freezed or self.descriptionTextEdit.toPlainText() == '':
            self.descriptionTextEdit.blockSignals(True)
            self.descriptionTextEdit.setText(self.item.get_description())
            self.unfreeze_text_edit()
            self.unset_edit_mode()
            self.descriptionTextEdit.blockSignals(False)

    def customize_without_item(self):
        self.unfreeze_text_edit()
        self.unset_edit_mode()

    def create_rich_edit(self):
        self.ui_richedit = Ui_richeditWidget(self.descriptionTextEdit, parent=self.descriptionTextEdit)
        # self.editorLayout.setParent(self.descriptionTextEdit)
        # self.editorLayout.addWidget(self.ui_richedit)

    def keyPressEvent(self, key):
        if key.key() == QtCore.Qt.Key_Escape:
            if self.item:
                self.customize_with_item()
            else:
                self.customize_without_item()

    def create_float_buttons(self):
        self.descriptionTextEdit.setViewportMargins(0, 20, 0, 24)
        self.clear_button_layout = QtGui.QGridLayout(self.descriptionTextEdit)
        self.clear_button_layout.setContentsMargins(0, 0, 0, 0)
        self.clear_button_layout.setSpacing(0)

        self.clear_button = QtGui.QToolButton()
        self.clear_button.setAutoRaise(True)
        self.clear_button.setFixedSize(24, 24)
        self.clear_button.setIcon(
            gf.get_icon('lock-open', icons_set='mdi'))

        self.clear_button_layout.addWidget(self.clear_button, 1, 3, 1, 1)
        self.clear_button_layout.addItem(QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum), 1, 4, 1, 1)

        self.lock_button = QtGui.QToolButton()
        self.lock_button.setAutoRaise(True)
        self.lock_button.setFixedSize(24, 24)
        self.lock_button.setIcon(
            gf.get_icon('lock', icons_set='mdi'))

        self.clear_button_layout.addWidget(self.lock_button, 1, 2, 1, 1)
        # self.clear_button_layout.addItem(QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum), 1, 3, 1, 1)

        self.edit_button = QtGui.QToolButton()
        self.edit_button.setAutoRaise(True)
        self.edit_button.setFixedSize(24, 24)
        self.edit_button.setIcon(
            gf.get_icon('pencil', icons_set='mdi'))

        self.clear_button_layout.addWidget(self.edit_button, 1, 0, 1, 1)
        self.clear_button_layout.addItem(QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 0, 0, 1, 3)

        self.save_button = QtGui.QToolButton()
        self.save_button.setAutoRaise(True)
        self.save_button.setFixedSize(24, 24)
        self.save_button.setIcon(
            gf.get_icon('content-save', icons_set='mdi', color=Qt4Gui.QColor(0, 255, 128, 192)))
        self.clear_button_layout.addWidget(self.save_button, 1, 1, 1, 1)

        self.clear_button.setHidden(True)
        self.save_button.setHidden(True)
        self.lock_button.setHidden(True)

    def description_update_finished(self):
        pass

    def update_desctiption(self):

        def update_desctiption_agent():
            return tc.update_description(
                search_key=self.item.get_search_key(),
                description=self.descriptionTextEdit.toPlainText()
                # description=gf.simplify_html(self.descriptionTextEdit.toHtml())
            )

        query_sobjects_worker = gf.get_thread_worker(
            update_desctiption_agent,
            finished_func=self.description_update_finished,
            error_func=gf.error_handle
        )
        self.item.update_description(self.descriptionTextEdit.toPlainText())
        query_sobjects_worker.start()

    def set_edit_mode(self):
        if not self.descriptionTextEdit_edited and not self.descriptionTextEdit_freezed:
            #print 'SETTING EDIT MODE'
            # self.unfreeze_text_edit()
            self.descriptionTextEdit.setStyleSheet('QTextEdit{border: 2px solid rgba(0,255,128,192); border-radius: 3px;}')
            self.descriptionTextEdit_edited = True
            self.edit_button.setHidden(True)
            self.save_button.setHidden(False)
            self.lock_button.setHidden(False)

    def unset_edit_mode(self):
        self.descriptionTextEdit.setStyleSheet('')
        self.descriptionTextEdit_edited = False
        self.edit_button.setHidden(False)
        self.save_button.setHidden(True)
        self.lock_button.setHidden(True)

    def freeze_text_edit(self):
        # if not self.descriptionTextEdit_edited:
            self.descriptionTextEdit.setStyleSheet('QTextEdit{border: 2px solid rgba(0,192,255,192); border-radius: 3px;}')
            self.descriptionTextEdit_freezed = True
            self.clear_button.setHidden(False)
            self.lock_button.setHidden(True)
            self.edit_button.setHidden(True)

    # def text_edit_select(self):
    #     if not self.descriptionTextEdit_edited and not self.descriptionTextEdit_freezed:
    #         self.descriptionTextEdit.clear()

    def get_description(self, fmt='html'):
        if self.descriptionTextEdit_freezed:
            if fmt == 'html':
                return self.descriptionTextEdit.toHtml()
            elif fmt == 'plain':
                return self.descriptionTextEdit.toPlainText()
        else:
            return 'No Description'

    def set_description(self, description):
        self.descriptionTextEdit.setText(description)
        self.descriptionTextEdit_freezed = True

    def unfreeze_text_edit(self):
        self.descriptionTextEdit.setStyleSheet('')
        self.descriptionTextEdit_freezed = False
        # self.clear_button.setHidden(True)
        if not self.descriptionTextEdit_edited:
            self.edit_button.setHidden(False)
