from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore

import lib.tactic_classes as tc
import lib.global_functions as gf
from lib.environment import env_inst, env_tactic


# edit/input widgets
class QtTacticEditWidget(QtGui.QWidget):
    def __init__(self, tactic_widget=None, qt_widgets=None, stype=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.tactic_widget = tactic_widget

        self.add_sobj_widget = parent
        self.sobject = self.tactic_widget.get_sobject()
        self.stype = stype

        self.qt_widgets = qt_widgets
        self.has_upload_wdg = None
        self.init_data = None
        self.shown = False

    def create_ui(self):
        self.shown = True
        self.create_main_layout()
        self.create_scroll_area()

        self.create_control_buttons()
        self.controls_actions()

        self.add_widgets_to_scroll_area()

        if self.get_view() == 'edit':
            self.init_data = self.get_data()

    def showEvent(self, event):
        if not self.shown:
            self.create_ui()

    def controls_actions(self):
        self.addNewButton.clicked.connect(self.commit_insert)
        self.saveButton.clicked.connect(self.commit_update)
        self.cancelButton.clicked.connect(lambda: self.add_sobj_widget.close())
        self.buildDirectoryButton.clicked.connect(self.build_directory_structure)

    def get_view(self):
        return self.tactic_widget.view

    def get_data(self):
        data = {}
        ignore = ['preview', 'parent']

        for widget in self.qt_widgets:
            column = widget.get_column()
            if column not in ignore:
                wdg_data = widget.get_data()
                if wdg_data:
                    data[column] = wdg_data
            else:
                self.has_upload_wdg = widget

        return data

    def commit_upload_wdg(self, sobject):
        if self.has_upload_wdg:
            if self.has_upload_wdg.tactic_widget.get_class_name() == 'tactic.ui.widget.upload_wdg.SimpleUploadWdg':
                search_key = sobject.get('__search_key__')
                self.has_upload_wdg.checkin_icon_file(search_key)

    @gf.catch_error
    def commit_update(self):
        data = self.get_data()

        if self.check_name_uniqueness(data):
            existing_sobject = self.tactic_widget.commit(data)

            self.commit_upload_wdg(existing_sobject)

            self.add_sobj_widget.refresh_results()
            self.add_sobj_widget.close()

    @gf.catch_error
    def build_directory_structure(self):
        import os
        repo = self.repositoryComboBox.itemData(self.repositoryComboBox.currentIndex())
        if self.stype.pipeline:
            paths = tc.get_dirs_with_naming(self.sobject.get_search_key())
            for path in paths:
                abs_path = repo['value'][0] + '/' + path
                if not os.path.exists(gf.form_path(abs_path)):
                    os.makedirs(gf.form_path(abs_path))

    def check_name_uniqueness(self, data):
        name = data.get('name')
        if not name:
            return True
        search_type = self.tactic_widget.get_search_type()

        if not search_type and self.sobject:
            search_type = tc.server_start().split_search_key(self.sobject.get_search_key())
            search_type = search_type[0]

        if name and search_type:
            filters = [('name', name)]
            existing = tc.server_start().query(search_type, filters)

            if self.get_view() == 'edit':
                # check if we editing and leaved the same name, not warn about uniqueness
                if self.init_data.get('name') == name:
                    existing = False

            if existing:
                msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'This Name already used!',
                                        "Do you want to use this name anyway?",
                                        QtGui.QMessageBox.NoButton, self)
                msb.addButton("Yes", QtGui.QMessageBox.YesRole)
                msb.addButton("No", QtGui.QMessageBox.NoRole)
                msb.exec_()
                reply = msb.buttonRole(msb.clickedButton())

                if reply == QtGui.QMessageBox.YesRole:
                    return True
                elif reply == QtGui.QMessageBox.NoRole:
                    return False

            return True

    @gf.catch_error
    def commit_insert(self):

        # TODO Parent key, search key
        data = self.get_data()

        if self.check_name_uniqueness(data):
            new_sobject = self.tactic_widget.commit(data)

            self.commit_upload_wdg(new_sobject)
            if self.add_sobj_widget.item:
                if self.add_sobj_widget.item.type == 'child':
                    self.add_sobj_widget.refresh_results()
            else:
                self.add_sobj_widget.add_new_tab(new_sobject)
            self.add_sobj_widget.close()

    def create_control_buttons(self):
        self.addNewButton = QtGui.QPushButton('Create')
        self.addNewButton.setMaximumWidth(80)
        self.saveButton = QtGui.QPushButton('Save')
        self.saveButton.setMaximumWidth(80)
        self.cancelButton = QtGui.QPushButton('Cancel')
        self.cancelButton.setMaximumWidth(80)
        self.buildDirectoryButton = QtGui.QPushButton('Build Full Directory Structure')
        self.buildDirectoryButton.setIcon(gf.get_icon('database'))
        self.build_directory_checkbox = QtGui.QCheckBox('Build Full Directory Structure')
        self.build_directory_checkbox.setChecked(False)
        self.build_directory_checkbox.setIcon(gf.get_icon('database'))
        self.repositoryComboBox = QtGui.QComboBox()
        base_dirs = env_tactic.get_all_base_dirs()
        # Default repo states
        from lib.configuration import cfg_controls
        current_repo = gf.get_value_from_config(cfg_controls.get_checkin(), 'repositoryComboBox')
        for key, val in base_dirs:
            if val['value'][4]:
                self.repositoryComboBox.addItem(val['value'][1])
                self.repositoryComboBox.setItemData(self.repositoryComboBox.count() - 1, val)
        if current_repo:
            self.repositoryComboBox.setCurrentIndex(current_repo)

        if self.tactic_widget.view == 'insert':
            self.main_layout.addWidget(self.build_directory_checkbox, 1, 0, 1, 1)
            self.main_layout.addWidget(self.repositoryComboBox, 1, 1, 1, 1)
            spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
            self.main_layout.addItem(spacerItem, 1, 2, 1, 1)
            self.main_layout.addWidget(self.addNewButton, 1, 3, 1, 1)
            self.main_layout.addWidget(self.cancelButton, 1, 4, 1, 1)
            self.main_layout.setColumnStretch(1, 0)
        else:
            self.main_layout.addWidget(self.buildDirectoryButton, 1, 0, 1, 1)
            self.main_layout.addWidget(self.repositoryComboBox, 1, 1, 1, 1)
            spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
            self.main_layout.addItem(spacerItem, 1, 2, 1, 1)
            self.main_layout.addWidget(self.saveButton, 1, 3, 1, 1)
            self.main_layout.addWidget(self.cancelButton, 1, 4, 1, 1)
            self.main_layout.setColumnStretch(1, 0)

    def add_widgets_to_scroll_area(self):
        for widget in self.qt_widgets:
            widget.setParent(self)
            self.scroll_area_layout.addWidget(widget)

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(9, 9, 9, 9)

    def create_scroll_area(self):
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area_contents = QtGui.QWidget()
        self.scroll_area_layout = QtGui.QVBoxLayout(self.scroll_area_contents)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_contents)
        self.scroll_area_layout.setAlignment(QtCore.Qt.AlignTop)

        self.main_layout.addWidget(self.scroll_area, 0, 0, 1, 0)

    def set_settings_from_dict(self, settings_dict=None):
        if not settings_dict:
            settings_dict = {
                'build_directory_checkbox': False,
            }

        self.build_directory_checkbox.setChecked(settings_dict.get('build_directory_checkbox'))

    def get_settings_dict(self):
        settings_dict = {
            'build_directory_checkbox': self.build_directory_checkbox.isChecked(),
        }
        return settings_dict


class QTacticBasicInputWdg(object):
    def __init__(self):
        self.init_ui()

    def init_ui(self):
        self.create_main_layout()
        self.create_label()

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(9, 9, 9, 9)
        self.main_layout.setColumnStretch(1, 1)

    def create_label(self):
        self.label = QtGui.QLabel()
        self.main_layout.addWidget(self.label, 0, 0)
        self.label.setMinimumWidth(100)
        self.label.setAlignment(QtCore.Qt.AlignRight)

    def create_conrol(self, control_widget):
        self.main_layout.addWidget(control_widget, 0, 1)

    def set_control_widget(self, control_widget):
        self.create_conrol(control_widget)

    def set_title(self, title):
        self.label.setText(title)


class QTacticSelectWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()

        self.parent_ui = parent

        self.tactic_widget = tactic_widget
        self.parent_sobject = self.tactic_widget.get_parent_sobject()
        self.sobject = self.tactic_widget.get_sobject()

        self.create_combo_box()

        self.set_title(self.tactic_widget.get_title())
        self.set_control_widget(self.combo_box)

        self.add_items_to_combo_box()

        self.autofill_by_parent()
        self.autofill_when_edit()

    def autofill_by_parent(self):
        if self.parent_sobject:
            parent_code = self.parent_sobject.info.get('code')
            if parent_code:
                for i, value in enumerate(self.tactic_widget.get_values()):
                    if parent_code == value:
                        self.combo_box.setCurrentIndex(i)

    def autofill_when_edit(self):

        sobject = self.parent_sobject
        if not sobject:
            sobject = self.sobject

        if sobject:
            column = sobject.info.get(self.get_column())
            if column:
                for i, value in enumerate(self.tactic_widget.get_values()):
                    if column == value:
                        self.combo_box.setCurrentIndex(i)

    def get_data(self):
        if self.combo_box.currentIndex() > 0:
            codes = self.tactic_widget.get_values()
            index = self.combo_box.currentIndex()
            return codes[index]
        else:
            return ''

    def get_column(self):
        action_options = self.tactic_widget.get_action_options()
        column = action_options.get('column')
        if column:
            return column

    def create_combo_box(self):
        self.combo_box = QtGui.QComboBox()
        self.combo_box.setEditable(True)
        self.combo_box.setCurrentIndex(0)

    def add_items_to_combo_box(self):
        labels = self.tactic_widget.get_labels()
        for label in labels:
            self.combo_box.addItem(label)


class QTacticSimpleUploadWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        self.create_upload_wdg()

        self.set_title(self.tactic_widget.get_title())
        self.set_control_widget(self.upload_wdg)

        self.controls_actions()

        self.setAcceptDrops(True)

    def controls_actions(self):

        self.browse_button.clicked.connect(self.browse_for_preview)

    def get_data(self):
        return None

    def get_column(self):
        return self.tactic_widget.get_name()

    @gf.catch_error
    def browse_for_preview(self):
        options = QtGui.QFileDialog.Options()
        options |= QtGui.QFileDialog.DontUseNativeDialog
        file_name, filter = QtGui.QFileDialog.getOpenFileName(self, 'Browse for Preview Image',
                                                              self.text_edit.text(),
                                                              'All Images (*.jpg | *.jpeg | *.png);;'
                                                              'JPEG Files (*.jpg | *.jpeg);;'
                                                              'PNG Files (*.png)',
                                                              '', options)
        if file_name:
            self.text_edit.setText(file_name)

    def create_upload_wdg(self):
        self.create_browse_button()
        self.create_edit()
        self.create_drop_plate()

        self.upload_wdg = QtGui.QWidget()
        self.upload_wdg_layout = QtGui.QGridLayout()
        self.upload_wdg.setLayout(self.upload_wdg_layout)
        self.upload_wdg_layout.setSpacing(6)
        self.upload_wdg_layout.setContentsMargins(0, 0, 0, 0)

        self.upload_wdg_layout.addWidget(self.browse_button, 0, 0, 1, 1)
        self.upload_wdg_layout.addWidget(self.text_edit, 0, 1, 1, 1)
        self.upload_wdg_layout.addWidget(self.drop_plate, 1, 0, 1, 2)

    def create_edit(self):
        self.text_edit = QtGui.QLineEdit()

    def create_drop_plate(self):
        self.drop_plate = QtGui.QWidget()
        self.drop_plate.setMinimumWidth(200)
        self.drop_plate.setMinimumHeight(50)
        self.drop_plate_layout = QtGui.QHBoxLayout()
        self.drop_plate_layout.setSpacing(0)
        self.drop_plate_layout.setContentsMargins(0, 0, 0, 0)
        self.drop_plate.setLayout(self.drop_plate_layout)
        self.drop_plate_label = QtGui.QLabel('DROP HERE')
        self.drop_plate_label.setAlignment(QtCore.Qt.AlignCenter)
        self.drop_plate_layout.addWidget(self.drop_plate_label)
        self.drop_plate_label.setStyleSheet('QLabel{border: 1px solid gray;border-radius: 4px;background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 0, 0, 32), stop:1 rgba(0, 0, 0, 0));}')

    def fill_text_edit(self, links_list):
        # for link in links_list:
        self.text_edit.setText(links_list[0])

    def get_upload_list(self):
        if self.text_edit.text():
            return [self.text_edit.text()]

    def checkin_icon_file(self, search_key):
        stype = self.tactic_widget.get_stype()

        checkin_widget = env_inst.get_check_tree(tab_code='checkin_out', wdg_code=stype.info.get('code'))

        files_list = self.get_upload_list()

        if files_list:
            checkin_widget.checkin_from_path(search_key, 'icon', '', files_list)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(unicode(url.toLocalFile()))
            self.fill_text_edit(links)
        else:
            event.ignore()

    def create_browse_button(self):
        self.browse_button = QtGui.QPushButton('Browse')


class QTacticTextWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        self.create_text_edit()

        self.set_title(self.tactic_widget.get_title())
        self.fill_default_values()
        self.set_control_widget(self.text_edit)

    def get_data(self):
        return unicode(self.text_edit.text())

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):
        values = self.tactic_widget.get_values()
        if values:
            self.text_edit.setText(str(values[0]))

    def create_text_edit(self):
        self.text_edit = QtGui.QLineEdit()


class QTacticTextAreaWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        self.create_text_area()

        self.set_title(self.tactic_widget.get_title())
        self.fill_default_values()
        self.set_control_widget(self.text_area)

    def get_data(self):
        return unicode(self.text_area.toPlainText())

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):
        values = self.tactic_widget.get_values()
        if values:
            self.text_area.setText(values[0])

    def create_text_area(self):
        self.text_area = QtGui.QTextEdit()


class QTacticCurrentCheckboxWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        # self.create_text_area()

        self.set_title(self.tactic_widget.get_title())
        # self.fill_default_values()
        # self.set_control_widget(self.text_area)

    def get_data(self):
        return 0

    def get_column(self):
        return self.tactic_widget.get_name()
    #
    # def fill_default_values(self):
    #     values = self.tactic_widget.get_values()
    #     if values:
    #         self.text_area.setText(values[0])
    #
    # def create_text_area(self):
    #     self.text_area = QtGui.QTextEdit()


class QTacticTaskSObjectInputWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()

        self.parent_ui = parent

        self.tactic_widget = tactic_widget

        self.create_parent_label()

        self.set_title(self.tactic_widget.get_title())
        self.fill_default_values()
        self.set_control_widget(self.parent_label)

    def get_data(self):
        values = self.tactic_widget.get_values()
        if values:
            return values[0]

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):
        sobject = self.tactic_widget.get_sobject()
        parent_sobject = self.tactic_widget.get_parent_sobject()

        if parent_sobject:
            if self.parent_ui.get_view() == 'edit':
                title = parent_sobject.info.get('name')
                if not title:
                    title = parent_sobject.info.get('title')
                elif not title:
                    title = parent_sobject.info.get('code')
                self.parent_label.setText(title)

        if sobject:
            if not parent_sobject and self.parent_ui.get_view() == 'edit':
                title = sobject.info.get('search_code')
                self.parent_label.setText(title)

            if sobject.info['__search_key__'] == self.get_data():
                title = sobject.info.get('name')
                if not title:
                    title = sobject.info.get('title')
                elif not title:
                    title = sobject.info.get('code')
                self.parent_label.setText(title)

    def create_parent_label(self):
        self.parent_label = QtGui.QLabel()
