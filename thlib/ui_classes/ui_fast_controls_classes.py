from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui

import thlib.global_functions as gf
from thlib.ui.checkin_out.ui_fast_controls import Ui_fastControls


class Ui_fastControlsWidget(QtGui.QWidget, Ui_fastControls):
    def __init__(self, stype, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        self.project = project
        self.item = None

        self.create_ui()

    def create_ui(self):
        self.setupUi(self)
        # self.customize_ui()

        # self.fill_process_combo_box()
        self.create_explicit_filename_edit()
        self.create_context_combo_box()
        self.controls_actions()

    def controls_actions(self):

        self.contextComboBox.editTextChanged.connect(self.freeze_context_combo_box)
        self.contextComboBox_clear_button.clicked.connect(self.unfreeze_context_combo_box)
        self.explicitFilenameLineEdit.textEdited.connect(self.freeze_explicit_filename_edit)
        self.explicitFilenameLineEdit_clear_button.clicked.connect(self.unfreeze_explicit_filename_edit)

    def set_item(self, item):
        self.item = item
        if self.item:
            self.customize_with_item()
        else:
            self.customize_without_item()

    def customize_with_item(self):
        self.contextComboBox.setEnabled(True)
        self.processComboBox.setEnabled(True)

        if not self.contextComboBox_freezed:
            self.fill_context_combo_box(self.item.get_context_options(), self.item.get_context())
            self.unfreeze_context_combo_box()

        self.fill_process_combo_box(self.item.get_full_process_list(), self.item.get_current_process_info())

        if self.item.type in ['snapshot', 'sobject', 'process']:
            checkin_mode = self.item.get_checkin_mode_options()
            self.set_checkin_mode(checkin_mode)

    def customize_without_item(self):

        self.contextComboBox.setEnabled(False)
        self.processComboBox.setEnabled(False)
        self.unfreeze_context_combo_box()
        self.unfreeze_explicit_filename_edit()
        self.clear_explicit_filename()

    def fill_context_combo_box(self, contexts_list, current_context=None):
        self.contextComboBox.clear()
        if contexts_list:
            self.contextComboBox.addItems(contexts_list)

        if current_context != None:
            if current_context == '':
                self.contextComboBox.setEditText('')
            else:
                self.contextComboBox.addItem(current_context)
                self.contextComboBox.setCurrentIndex(self.contextComboBox.count()-1)

    def fill_process_combo_box(self, process_dict, current_process=None):
        if current_process:
            current_process = current_process.get('name')

        if process_dict:
            process_list = process_dict.keys()
            process_list.append('publish')
        else:
            process_list = ['publish']  # may be need to add attachment

        self.processComboBox.clear()
        for i, process in enumerate(process_list):
            self.processComboBox.addItem(process)
            if current_process and current_process == process:
                self.processComboBox.setCurrentIndex(i)

    def create_explicit_filename_edit(self):
        self.explicitFilenameLineEdit_freezed = False
        self.explicitFilenameLineEdit.clear()

        self.explicitFilenameLineEdit_clear_button_layout = QtGui.QHBoxLayout(self.explicitFilenameLineEdit)
        self.explicitFilenameLineEdit_clear_button_layout.setContentsMargins(0, 0, 3, 0)
        self.explicitFilenameLineEdit_clear_button_layout.setSpacing(0)
        self.explicitFilenameLineEdit_clear_button = QtGui.QToolButton()
        self.explicitFilenameLineEdit_clear_button.setFixedSize(16, 16)
        self.explicitFilenameLineEdit_clear_button.setIcon(gf.get_icon('remove', icons_set='ei', color=Qt4Gui.QColor(255, 196, 0, 192), scale_factor=0.8))
        self.explicitFilenameLineEdit_clear_button_layout.insertStretch(0)
        self.explicitFilenameLineEdit_clear_button_layout.addWidget(self.explicitFilenameLineEdit_clear_button)
        self.explicitFilenameLineEdit_clear_button.setHidden(True)

        # if env_mode.get_mode() == 'standalone':
        #     self.explicitFilenameLabel.setHidden(True)
        #     self.explicitFilenameLineEdit.setHidden(True)

    def freeze_explicit_filename_edit(self):
        self.explicitFilenameLineEdit.setStyleSheet('QLineEdit{border-color: rgba(0,192,255,192);}')
        self.explicitFilenameLineEdit_freezed = True
        self.explicitFilenameLineEdit_clear_button.setHidden(False)

    def unfreeze_explicit_filename_edit(self):
        self.explicitFilenameLineEdit.setStyleSheet('')
        self.explicitFilenameLineEdit_freezed = False
        self.explicitFilenameLineEdit_clear_button.setHidden(True)
        self.explicitFilenameLineEdit.clear()

    def create_context_combo_box(self):
        self.contextComboBox_freezed = False
        self.contextComboBox.clear()

        self.contextComboBox_clear_button_layout = QtGui.QHBoxLayout(self.contextComboBox)
        self.contextComboBox_clear_button_layout.setContentsMargins(0, 0, 20, 0)
        self.contextComboBox_clear_button_layout.setSpacing(0)
        self.contextComboBox_clear_button = QtGui.QToolButton()
        self.contextComboBox_clear_button.setFixedSize(16, 16)
        self.contextComboBox_clear_button.setIcon(gf.get_icon('unlock', icons_set='ei', color=Qt4Gui.QColor(0, 196, 255, 192), scale_factor=0.8))
        self.contextComboBox_clear_button_layout.insertStretch(0)
        self.contextComboBox_clear_button_layout.addWidget(self.contextComboBox_clear_button)
        self.contextComboBox_clear_button.setHidden(True)

    def freeze_context_combo_box(self):
        self.contextComboBox.setStyleSheet('QComboBox{background-color: rgba(0,192,255,192);}')
        self.contextComboBox_freezed = True
        self.contextComboBox_clear_button.setHidden(False)

    def unfreeze_context_combo_box(self):
        self.contextComboBox.setStyleSheet('')
        self.contextComboBox_freezed = False
        self.contextComboBox_clear_button.setHidden(True)

    def set_checkin_mode(self, checkin_mode):
        if not checkin_mode or checkin_mode == 'file':
            self.checkinTypeComboBox.setCurrentIndex(0)
        elif checkin_mode == 'sequence':
            self.checkinTypeComboBox.setCurrentIndex(1)
        elif checkin_mode == 'dir':
            self.checkinTypeComboBox.setCurrentIndex(2)
        elif checkin_mode == 'multi_file':
            self.checkinTypeComboBox.setCurrentIndex(3)
        elif checkin_mode == 'workarea':
            self.checkinTypeComboBox.setCurrentIndex(4)

    def get_checkin_mode(self):
        if self.checkinTypeComboBox.currentIndex() == 0:
            return 'file'
        elif self.checkinTypeComboBox.currentIndex() == 1:
            return 'sequence'
        elif self.checkinTypeComboBox.currentIndex() == 2:
            return 'dir'
        elif self.checkinTypeComboBox.currentIndex() == 3:
            return 'multi_file'
        elif self.checkinTypeComboBox.currentIndex() == 4:
            return 'workarea'

    def get_context(self):
        return self.contextComboBox.currentText()

    def clear_explicit_filename(self):
        self.explicitFilenameLineEdit.setText('')

    def get_explicit_filename(self):
        explicit_name = self.explicitFilenameLineEdit.text()
        if explicit_name:
            self.explicitFilenameLineEdit.setText(explicit_name.replace(' ', '_').replace('/', '_').replace('\\', '_'))
        return self.explicitFilenameLineEdit.text()
