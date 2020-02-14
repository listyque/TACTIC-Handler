from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

import thlib.tactic_classes as tc
import thlib.global_functions as gf
from thlib.ui_classes.ui_richedit_classes import Ui_richeditWidget


class Ui_tacticColumnEditorWidget(QtGui.QWidget):
    def __init__(self, sobject=None, column=None, stype=None, parent=None, multiple_mode=False):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui_raw()

        self.sobject = sobject
        self.column = column
        self.stype = stype

        self.multiple_mode = multiple_mode

        self.old_data = None
        self.new_data = None

        self.descriptionTextEdit_freezed = False
        self.descriptionTextEdit_edited = False

        self.create_ui()

    def create_ui_raw(self):
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")

        self.editorLayout = QtGui.QVBoxLayout()
        self.editorLayout.setSpacing(0)
        self.editorLayout.setObjectName("editorLayout")
        self.verticalLayout.addLayout(self.editorLayout)

        # self.verticalLayout.setStretch(1, 1)

    def create_ui(self):

        self.create_plain_text_editor()

        self.create_float_buttons()

        if self.sobject:
            self.customize_with_sobject()

        # self.create_rich_edit()

        self.controls_actions()

    def controls_actions(self):
        self.plain_text_editor.cursorPositionChanged.connect(self.set_edit_mode)
        self.plain_text_editor.textChanged.connect(self.data_changed)
        # self.descriptionTextEdit.selectionChanged.connect(self.text_edit_select)
        self.clear_button.clicked.connect(self.unfreeze_text_edit)

        self.lock_button.clicked.connect(self.freeze_text_edit)

        self.edit_button.clicked.connect(self.set_edit_mode)
        self.save_button.clicked.connect(self.save_current_column)

    def set_sobject(self, sobject):
        self.sobject = sobject

        self.customize_with_sobject()

    def get_sobject(self):
        return self.sobject

    def get_column(self):
        return self.column

    def get_changed_data(self):

        if self.old_data != self.new_data:
            return self.new_data
        else:
            return None

    def customize_with_sobject(self):

        # Getting column info

        column_info = self.stype.get_column_info(self.column)

        text_editor_columns = ['text', 'varchar']

        if column_info['data_type'] in text_editor_columns:
            self.create_text_editor_column()

        # if not self.descriptionTextEdit_freezed or self.descriptionTextEdit.toPlainText() == '':
        #     self.descriptionTextEdit.blockSignals(True)
        #     self.descriptionTextEdit.setText(self.item.get_description())
        #     self.unfreeze_text_edit()
        #     self.unset_edit_mode()
        #     self.descriptionTextEdit.blockSignals(False)

    # def set_item(self, item):
    #     if not self.visibleRegion().isEmpty():
    #         self.item = item
    #         if self.item:
    #             self.customize_with_item()
    #         else:
    #             self.customize_without_item()
    #
    # def customize_with_item(self):
    #
    #     if not self.descriptionTextEdit_freezed or self.descriptionTextEdit.toPlainText() == '':
    #         self.descriptionTextEdit.blockSignals(True)
    #         self.descriptionTextEdit.setText(self.item.get_description())
    #         self.unfreeze_text_edit()
    #         self.unset_edit_mode()
    #         self.descriptionTextEdit.blockSignals(False)

    def create_plain_text_editor(self):
        self.plain_text_editor = QtGui.QTextEdit(self)
        self.plain_text_editor.setObjectName('plain_text_editor')

        self.verticalLayout.addWidget(self.plain_text_editor)

    def create_text_editor_column(self):
        if not self.multiple_mode:
            self.old_data = self.sobject.get_value(self.column)
            self.new_data = self.sobject.get_value(self.column)
            self.plain_text_editor.setText(self.old_data)

    def customize_without_item(self):
        self.unfreeze_text_edit()
        self.unset_edit_mode()

    def create_rich_edit(self):
        self.plain_text_editor.setViewportMargins(0, 20, 0, 24)
        self.ui_richedit = Ui_richeditWidget(self.plain_text_editor, parent=self.plain_text_editor)
        # self.editorLayout.setParent(self.descriptionTextEdit)
        # self.editorLayout.addWidget(self.ui_richedit)

    def keyPressEvent(self, key):
        if key.key() == QtCore.Qt.Key_Escape:
            if self.item:
                self.customize_with_item()
            else:
                self.customize_without_item()

    def create_float_buttons(self):
        self.clear_button_layout = QtGui.QGridLayout(self.plain_text_editor)
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

    def data_changed(self):
        self.new_data = self.plain_text_editor.toPlainText()

    def set_edit_mode(self):
        if not self.descriptionTextEdit_edited and not self.descriptionTextEdit_freezed:
            #print 'SETTING EDIT MODE'
            # self.unfreeze_text_edit()
            self.plain_text_editor.setStyleSheet('QTextEdit{border: 2px solid rgba(0,255,128,192); border-radius: 3px;}')
            self.descriptionTextEdit_edited = True
            self.edit_button.setHidden(True)
            self.save_button.setHidden(False)
            self.lock_button.setHidden(False)

    def unset_edit_mode(self):
        self.plain_text_editor.setStyleSheet('')
        self.descriptionTextEdit_edited = False
        self.edit_button.setHidden(False)
        self.save_button.setHidden(True)
        self.lock_button.setHidden(True)

    def freeze_text_edit(self):
        # if not self.descriptionTextEdit_edited:
            self.plain_text_editor.setStyleSheet('QTextEdit{border: 2px solid rgba(0,192,255,192); border-radius: 3px;}')
            self.descriptionTextEdit_freezed = True
            self.clear_button.setHidden(False)
            self.lock_button.setHidden(True)
            self.edit_button.setHidden(True)

    def save_current_column(self):
        self.unset_edit_mode()
        print 'SAVING CURRENT COLUMN'

    def unfreeze_text_edit(self):
        self.descriptionTextEdit.setStyleSheet('')
        self.descriptionTextEdit_freezed = False
        # self.clear_button.setHidden(True)
        if not self.descriptionTextEdit_edited:
            self.edit_button.setHidden(False)
