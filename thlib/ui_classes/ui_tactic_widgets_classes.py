from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore

import thlib.tactic_classes as tc
import thlib.global_functions as gf
from thlib.environment import env_inst, env_mode, env_tactic, cfg_controls
from thlib.ui_classes.ui_custom_qwidgets import Ui_previewsEditorDialog, Ui_screenShotMakerDialog, Ui_coloredComboBox, StyledComboBox


# edit/input widgets
class QtTacticEditWidget(QtGui.QWidget):
    def __init__(self, tactic_widget=None, qt_widgets=None, stype=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.tactic_widget = tactic_widget

        self.add_sobj_widget = parent
        self.sobject = self.tactic_widget.get_sobject()
        self.parent_sobject = self.tactic_widget.get_parent_sobject()
        self.stype = stype
        self.item = self.add_sobj_widget.item

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

    def get_sobject(self):
        return self.sobject

    def get_parent_sobject(self):
        return self.parent_sobject

    def get_stype(self):
        return self.stype

    def get_info_dict(self):
        return self.tactic_widget.get_info_dict()

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
                if wdg_data is not None:
                    data[column] = wdg_data
            else:
                self.has_upload_wdg = widget

        return data

    def commit_upload_wdg(self, sobject):
        if self.has_upload_wdg:
            if self.has_upload_wdg.tactic_widget.get_class_name() == 'tactic.ui.widget.upload_wdg.SimpleUploadWdg':
                search_key = sobject.get('__search_key__')
                return self.has_upload_wdg.checkin_icon_file(search_key)

    @gf.catch_error
    def commit_update(self):
        data = self.get_data()

        if self.check_name_uniqueness(data):
            existing_sobject = self.tactic_widget.commit(data)

            if not self.commit_upload_wdg(existing_sobject):
                self.add_sobj_widget.refresh_results()

            self.add_sobj_widget.close()

    @gf.catch_error
    def build_directory_structure(self, sobject=None):
        import os
        repo = self.repositoryComboBox.itemData(self.repositoryComboBox.currentIndex())
        if sobject:
            sobject_class = tc.SObject(sobject, project=self.stype.project)
            self.sobject = sobject_class

        if self.stype.pipeline:

            paths = tc.get_dirs_with_naming(self.sobject.get_search_key(), None)

            all_paths = []

            if paths:
                if paths['versionless']:
                    all_paths.extend(paths['versionless'])
                if paths['versions']:
                    all_paths.extend(paths['versions'])

            if not repo:
                base_dirs = env_tactic.get_all_base_dirs()
                for key, val in base_dirs:
                    if val['value'][4]:
                        for path in all_paths:
                            abs_path = val['value'][0] + '/' + path
                            if not os.path.exists(gf.form_path(abs_path)):
                                os.makedirs(gf.form_path(abs_path))
            else:
                for path in all_paths:
                    abs_path = repo['value'][0] + '/' + path
                    if not os.path.exists(gf.form_path(abs_path)):
                        os.makedirs(gf.form_path(abs_path))

    def check_name_uniqueness(self, data):
        existing = False

        name = data.get('name')
        if not name:
            return True
        search_type = self.tactic_widget.get_search_type()

        if not search_type and self.sobject:
            search_key_split = tc.split_search_key(self.sobject.get_search_key())
            search_type = search_key_split.get('search_type')

        if name and search_type:
            # better version, that take parents into account
            parent_sobject = self.tactic_widget.get_parent_sobject()
            if parent_sobject:
                related_sobjects, info = parent_sobject.get_related_sobjects(child_stype=self.stype, parent_stype=parent_sobject.get_stype())
            else:
                if self.sobject:
                    if self.sobject.get_value('name'):
                        filters = [('name', self.sobject.get_value('name'))]
                        related_sobjects, info = tc.get_sobjects(self.stype.get_code(), filters, project_code=self.stype.get_project().get_code())
                    else:
                        related_sobjects = {}
                else:
                    related_sobjects = {}

            for related_sobject in related_sobjects.values():
                if related_sobject.get_value('name') == name:
                    existing = True

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

            if self.build_directory_checkbox.isChecked():
                self.build_directory_structure(new_sobject)

    def create_control_buttons(self):
        self.addNewButton = QtGui.QPushButton('Create')
        self.addNewButton.setMaximumWidth(80)
        self.addNewButton.setFlat(True)
        self.addNewButton.setIcon(gf.get_icon('plus', icons_set='mdi', scale_factor=1))
        self.saveButton = QtGui.QPushButton('Save')
        self.saveButton.setMaximumWidth(80)
        self.saveButton.setFlat(True)
        self.saveButton.setIcon(gf.get_icon('content-save', icons_set='mdi', scale_factor=1))
        self.cancelButton = QtGui.QPushButton('Cancel')
        self.cancelButton.setMaximumWidth(80)
        self.cancelButton.setFlat(True)
        self.cancelButton.setIcon(gf.get_icon('cancel', icons_set='mdi', scale_factor=1))
        self.buildDirectoryButton = QtGui.QPushButton('Build Full Directory Structure')
        self.buildDirectoryButton.setIcon(gf.get_icon('folder-multiple', icons_set='mdi', scale_factor=1))
        self.buildDirectoryButton.setFlat(True)
        self.build_directory_checkbox = QtGui.QCheckBox('Build Full Directory Structure')
        self.build_directory_checkbox.setChecked(False)
        self.build_directory_checkbox.setIcon(gf.get_icon('folder-multiple', icons_set='mdi', scale_factor=1))

        self.repositoryComboBox = QtGui.QComboBox()
        base_dirs = env_tactic.get_all_base_dirs()
        # Default repo states
        current_repo = gf.get_value_from_config(cfg_controls.get_checkin(), 'repositoryComboBox')
        for key, val in base_dirs:
            if val['value'][4]:
                self.repositoryComboBox.addItem(val['value'][1])
                self.repositoryComboBox.setItemData(self.repositoryComboBox.count() - 1, val)

        # Special for build all repos dirs
        self.repositoryComboBox.addItem('All Repos')

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

        if self.item:
            if self.item.type != 'sobject':
                self.buildDirectoryButton.setHidden(True)
                self.repositoryComboBox.setHidden(True)

        if not self.stype.get_pipeline():
            self.buildDirectoryButton.setHidden(True)
            self.build_directory_checkbox.setHidden(True)
            self.repositoryComboBox.setHidden(True)

    def add_widgets_to_scroll_area(self):
        for widget in self.qt_widgets:
            widget.setParent(self)
            self.scroll_area_layout.addWidget(widget)

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(9, 9, 9, 9)

    def create_scroll_area(self):
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area.setStyleSheet("""
        QScrollArea {
            background: rgb(68, 68, 68);
        }
        QScrollArea > QWidget > QWidget {
            background: rgb(68, 68, 68);
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
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtGui.QScrollArea.NoFrame)

        self.scroll_area_contents = QtGui.QWidget()
        self.scroll_area_layout = QtGui.QVBoxLayout(self.scroll_area_contents)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_contents)
        self.scroll_area_layout.setAlignment(QtCore.Qt.AlignTop)

        self.main_layout.addWidget(self.scroll_area, 0, 0, 1, 0)

    def set_settings_from_dict(self, settings_dict=None):

        ref_settings_dict = {
            'build_directory_checkbox': False,
        }

        settings = gf.check_config(ref_settings_dict, settings_dict)

        self.build_directory_checkbox.setChecked(settings['build_directory_checkbox'])

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

        if not self.set_default_value():
            self.autofill_by_parent()

    # deprecated
    # def autofill_by_parent(self):
    #     if self.parent_sobject:
    #         parent_code = self.parent_sobject.info.get('code')
    #         if parent_code:
    #             for i, value in enumerate(self.tactic_widget.get_values()):
    #                 if parent_code == value:
    #                     self.combo_box.setCurrentIndex(i)
    #                     return True

    def autofill_by_parent(self):

        sobject = self.parent_sobject
        if not sobject:
            sobject = self.sobject

        if sobject:
            column = sobject.info.get(self.get_column())
            if column:
                for i, value in enumerate(self.tactic_widget.get_values()):
                    if column == value:
                        self.combo_box.setCurrentIndex(i)

    def set_default_value(self):

        default_value = self.tactic_widget.get_default_values()
        if default_value:
            for i, value in enumerate(self.tactic_widget.get_values()):
                if default_value == value:
                    self.combo_box.setCurrentIndex(i)
                    return True

    def get_data(self):

        codes = self.tactic_widget.get_values()
        index = self.combo_box.currentIndex()
        if codes:
            if not codes[index]:
                return ''
            else:
                return codes[index]

    def get_column(self):
        action_options = self.tactic_widget.get_action_options()
        column = action_options.get('column')
        if column:
            return column
        else:
            return self.tactic_widget.get_name()

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

        self.parent_ui = parent

        self.tactic_widget = tactic_widget
        self.links_to_upload_list = set()
        self.screenshots_to_upload_list = []

        self.create_upload_wdg()

        self.set_title(self.tactic_widget.get_title())
        self.set_control_widget(self.upload_wdg)

        self.controls_actions()

        self.setAcceptDrops(True)

    def controls_actions(self):

        self.choose_preview_button.clicked.connect(self.browse_for_preview)
        self.make_screenshot_button.clicked.connect(lambda: self.set_preview_to_commit_item('screenshot'))
        self.edit_previews_button.clicked.connect(self.edit_previews)
        self.clear_previews_button.clicked.connect(self.clear_all)

    def get_data(self):
        return None

    def get_column(self):
        return self.tactic_widget.get_name()

    def edit_previews(self):
        files_objects = self.get_upload_list_files_objects()
        screenshots = self.get_screenshots_to_upload_list()
        if files_objects or screenshots:
            self.edit_previews_dialog = Ui_previewsEditorDialog(
                files_objects=files_objects,
                screenshots=screenshots,
                parent=self)

            self.edit_previews_dialog.exec_()

    def clear_all(self):

        self.links_to_upload_list = set()
        self.screenshots_to_upload_list = []

        self.drop_plate_label.setText(
            'Drop Images Here ({0})'.format(len(self.get_upload_list()) + len(self.screenshots_to_upload_list)))

    @gf.catch_error
    def browse_for_preview(self):
        options = QtGui.QFileDialog.Options()
        options |= QtGui.QFileDialog.DontUseNativeDialog
        file_name, filter = QtGui.QFileDialog.getOpenFileName(self, 'Browse for Preview Image',
                                                              '',
                                                              'All Images (*.jpg | *.jpeg | *.png | *.tif);;'
                                                              'JPEG Images (*.jpg | *.jpeg);;'
                                                              'PNG Images (*.png);;'
                                                              'TIF Images (*.tif)',
                                                              '', options)
        if file_name:
            ext = gf.extract_extension(file_name)
            if ext[3] == 'preview':
                self.add_links_to_upload_list([file_name])

    def make_screenshot(self):
        screen_shot_maker_dialog = Ui_screenShotMakerDialog()

        # Hiding all app windows before making screenshot
        if env_mode.get_mode() == 'standalone':
            env_inst.ui_main.setHidden(True)
        elif env_mode.get_mode() == 'maya':
            env_inst.ui_maya_dock.setHidden(True)
        self.parent_ui.add_sobj_widget.setHidden(True)

        screen_shot_maker_dialog.exec_()

        if env_mode.get_mode() == 'standalone':
            env_inst.ui_main.setHidden(False)
        elif env_mode.get_mode() == 'maya':
            env_inst.ui_maya_dock.setHidden(False)
        self.parent_ui.add_sobj_widget.setHidden(False)

        self.screenshots_to_upload_list.append(screen_shot_maker_dialog.screenshot_pixmap)
        self.drop_plate_label.setText(
            'Drop Images Here ({0})'.format(len(self.get_upload_list()) + len(self.screenshots_to_upload_list)))

    def set_preview_to_commit_item(self, tp='screenshot'):
        if tp == 'screenshot':
            self.make_screenshot()
            # self.commit_item.set_preview(self.make_screenshot())

    def create_upload_wdg(self):

        self.make_screenshot_button = QtGui.QToolButton()
        self.make_screenshot_button.setAutoRaise(True)
        self.make_screenshot_button.setIcon(gf.get_icon('camera'))

        self.choose_preview_button = QtGui.QToolButton()
        self.choose_preview_button.setAutoRaise(True)
        self.choose_preview_button.setIcon(gf.get_icon('folder-open'))

        self.edit_previews_button = QtGui.QToolButton()
        self.edit_previews_button.setAutoRaise(True)
        self.edit_previews_button.setIcon(gf.get_icon('edit'))

        self.clear_previews_button = QtGui.QToolButton()
        self.clear_previews_button.setAutoRaise(True)
        self.clear_previews_button.setIcon(gf.get_icon('trash'))

        self.create_drop_plate()

        self.upload_wdg = QtGui.QWidget()
        self.upload_wdg_layout = QtGui.QHBoxLayout()
        self.upload_wdg.setLayout(self.upload_wdg_layout)
        self.upload_wdg_layout.setSpacing(6)
        self.upload_wdg_layout.setContentsMargins(0, 0, 0, 0)

        self.upload_wdg_layout.addWidget(self.make_screenshot_button)
        self.upload_wdg_layout.addWidget(self.choose_preview_button)
        self.upload_wdg_layout.addWidget(self.drop_plate)
        self.upload_wdg_layout.addWidget(self.edit_previews_button)
        self.upload_wdg_layout.addWidget(self.clear_previews_button)

    def create_drop_plate(self):
        self.drop_plate = QtGui.QWidget()
        self.drop_plate.setMinimumWidth(200)
        self.drop_plate.setMinimumHeight(32)
        self.drop_plate_layout = QtGui.QHBoxLayout()
        self.drop_plate_layout.setSpacing(0)
        self.drop_plate_layout.setContentsMargins(0, 0, 0, 0)
        self.drop_plate.setLayout(self.drop_plate_layout)
        self.drop_plate_label = QtGui.QLabel('Drop Images Here (0)')
        self.drop_plate_label.setAlignment(QtCore.Qt.AlignCenter)
        self.drop_plate_layout.addWidget(self.drop_plate_label)
        self.drop_plate_label.setStyleSheet('QLabel{border: 1px solid grey;border-radius: 4px;background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 0, 0, 16), stop:1 rgba(0, 0, 0, 24));}')

    def add_links_to_upload_list(self, links):
        for link in links:
            ext = gf.extract_extension(link)
            if ext[3] == 'preview':
                self.links_to_upload_list.add(link)

        self.links_to_upload_list = set(self.links_to_upload_list)

        self.drop_plate_label.setText(
            'Drop Images Here ({0})'.format(len(self.get_upload_list()) + len(self.screenshots_to_upload_list)))

    def get_upload_list(self):
        return self.links_to_upload_list

    def get_upload_list_files_objects(self):
        files_list = self.get_upload_list()

        if files_list:
            match_template = gf.MatchTemplate(['$FILENAME.$EXT'])
            return match_template.get_files_objects(files_list)

    def get_screenshots_to_upload_list(self):
        return self.screenshots_to_upload_list

    def checkin_icon_file(self, search_key):
        stype = self.tactic_widget.get_stype()

        checkin_widget = env_inst.get_check_tree(tab_code='checkin_out', wdg_code=stype.info.get('code'))

        files_list = self.get_upload_list()

        if files_list:
            match_template = gf.MatchTemplate(['$FILENAME.$EXT'])
            files_objects_dict = match_template.get_files_objects(files_list)
            commit_queue_ui = None
            for file_object in files_objects_dict.get('file'):
                commit_queue_ui = checkin_widget.checkin_file_objects(
                    search_key, 'icon', '', files_objects=[file_object], checkin_type='file', keep_file_name=False,
                    commit_silently=True, update_versionless=True)

            if commit_queue_ui:
                commit_queue_ui.commit_queue()

        return files_list

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
            if env_mode.py2:
                for url in event.mimeData().urls():
                    links.append(unicode(url.toLocalFile()))
            else:
                for url in event.mimeData().urls():
                    links.append(str(url.toLocalFile()))

            self.add_links_to_upload_list(links)
        else:
            event.ignore()


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
        if env_mode.py2:
            if unicode(self.text_edit.text()) != unicode(self.tactic_widget.get_default_values()):
                return unicode(self.text_edit.text())
        else:
            if str(self.text_edit.text()) != str(self.tactic_widget.get_default_values()):
                return str(self.text_edit.text())

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):
        if self.tactic_widget.get_default_values():
            if env_mode.py2:
                self.text_edit.setText(unicode(self.tactic_widget.get_default_values()))
            else:
                self.text_edit.setText(str(self.tactic_widget.get_default_values()))

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
        if env_mode.py2:
            if unicode(self.text_area.toPlainText()) != unicode(self.tactic_widget.get_default_values()):
                return unicode(self.text_area.toPlainText())
        else:
            if str(self.text_area.toPlainText()) != str(self.tactic_widget.get_default_values()):
                return str(self.text_area.toPlainText())

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):
        if self.tactic_widget.get_default_values():
            self.text_area.setText(self.tactic_widget.get_default_values())

    def create_text_area(self):
        self.text_area = QtGui.QTextEdit()


class QTacticCheckboxWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        self.create_checkbox()

        self.set_title(self.tactic_widget.get_title())
        self.fill_default_values()

        self.set_control_widget(self.checkbox)

    def get_data(self):
        return int(self.checkbox.isChecked())

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):
        values = self.tactic_widget.get_display_values()
        if values:
            self.checkbox.setChecked(values[0])
            self.checkbox.setText('                   ')

    def create_checkbox(self):
        self.checkbox = QtGui.QCheckBox()


class QTacticCurrentCheckboxWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        self.create_checkbox()

        self.set_title(self.tactic_widget.get_title())
        self.fill_default_values()

        self.set_control_widget(self.checkbox)

    def get_data(self):
        return int(self.checkbox.isChecked())

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):
        values = self.tactic_widget.get_display_values()
        if values:
            if isinstance(values, list):
                if isinstance(values[0], bool):
                    self.checkbox.setChecked(values[0])
                    self.checkbox.setText('                   ')

    def create_checkbox(self):
        self.checkbox = QtGui.QCheckBox()


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

        if not sobject or parent_sobject:
            display_values = self.tactic_widget.get_display_values()

            if display_values:
                if display_values[0]:
                    parent_sobject = self.tactic_widget.get_parent_sobject()
                    if parent_sobject:
                        self.parent_label.setText(parent_sobject.get_title())
                    else:
                        self.parent_label.setText(display_values[0])
                else:
                    stype = self.tactic_widget.get_stype()
                    project = stype.get_project()
                    self.parent_label.setText(project.get_title())
            else:
                parent_sobject = self.tactic_widget.get_parent_sobject()
                if parent_sobject:
                    self.parent_label.setText(parent_sobject.get_title())

    def create_parent_label(self):
        self.parent_label = QtGui.QLabel()


class QTacticCalendarInputWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        self.create_date_time_edit()

        self.set_title(self.tactic_widget.get_title())
        self.fill_default_values()

        self.set_control_widget(self.date_time_edit)

    def get_data(self):

        date_time = self.date_time_edit.dateTime()

        return date_time.toString('yyyy-MM-dd HH:mm:ss')

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):
        values = self.tactic_widget.get_display_values()

        if values:
            if values[0]:
                date = QtCore.QDateTime.fromString(gf.form_date_time(values[0]), 'yyyy-MM-dd HH:mm:ss')
                self.date_time_edit.setDateTime(date)

    def create_date_time_edit(self):
        self.date_time_edit = QtGui.QDateTimeEdit()
        self.date_time_edit.setDisplayFormat(u"yyyy.MM.dd. HH:mm:ss")
        self.date_time_edit.setCalendarPopup(True)
        current_datetime = QtCore.QDateTime.currentDateTime()
        self.date_time_edit.setDateTime(current_datetime)


class QTacticProcessGroupSelectWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()

        self.parent_ui = parent

        self.tactic_widget = tactic_widget
        self.parent_sobject = self.tactic_widget.get_parent_sobject()
        self.sobject = self.tactic_widget.get_sobject()

        self.create_combo_box()

        self.set_title(self.tactic_widget.get_title())
        self.set_control_widget(self.users_combo_box)

        self.fill_users_combo()

        # self.init_default_value()

        # if not self.init_default_value():
        #     self.autofill_by_parent()

    def autofill_by_parent(self):

        sobject = self.parent_sobject
        if not sobject:
            sobject = self.sobject

        if sobject:
            column = sobject.info.get(self.get_column())
            if column:
                for i, value in enumerate(self.tactic_widget.get_values()):
                    if column == value:
                        self.users_combo_box.setCurrentIndex(i)

    def init_default_value(self):

        display_values = self.tactic_widget.get_display_values()

        if display_values.get('labels'):
            default_value = display_values.get('labels')[0]

        else:
            default_value = None

        if default_value:
            for i, value in enumerate(self.tactic_widget.get_values()):
                if default_value == value:
                    self.users_combo_box.setCurrentIndex(i)
                    return True

    def get_data(self):
        if self.users_combo_box.currentIndex() not in [-1, 0]:
            idx = self.users_combo_box.currentIndex()
            return self.users_combo_box.itemData(idx-1, QtCore.Qt.UserRole)

    def get_column(self):
        action_options = self.tactic_widget.get_action_options()
        column = action_options.get('column')
        if column:
            return column
        else:
            return self.tactic_widget.get_name()

    def create_combo_box(self):
        self.users_combo_box = StyledComboBox()
        self.users_combo_box.setEditable(False)
        self.users_combo_box.setCurrentIndex(0)
        display_values = self.tactic_widget.get_value('__display_values__')
        if isinstance(display_values, dict):
            self.users_combo_box.addItem(display_values.get('empty_option_label'))
        else:
            print(display_values)

    def fill_users_combo(self):

        current_login = env_inst.get_current_login_object()

        stype = self.parent_sobject.get_stype()
        parent_sobject_pipeline_code = self.parent_sobject.get_pipeline_code()

        info_dict = self.parent_ui.get_info_dict()
        current_process = None
        if info_dict:
            current_process = info_dict.get('process')

        stype_current_pipeline = stype.get_pipeline()
        process_info = None
        if stype_current_pipeline:
            current_pipeline = stype_current_pipeline.get(parent_sobject_pipeline_code)
            process_info = current_pipeline.get_process_info(current_process)

        if process_info:
            assigned_login_group_code = process_info.get('assigned_login_group')
            assigned_login_group = current_login.get_login_group(assigned_login_group_code)

            if assigned_login_group:
                group_logins = assigned_login_group.get_logins()
                if group_logins:
                    for i, login in enumerate(group_logins):
                        self.users_combo_box.setItemData(i, login.get_login(), QtCore.Qt.UserRole)
                        self.users_combo_box.addItem(login.get_display_name())
            else:
                all_logins = env_inst.get_all_logins().values()
                for i, login in enumerate(all_logins):
                    self.users_combo_box.setItemData(i, login.get_login(), QtCore.Qt.UserRole)
                    self.users_combo_box.addItem(login.get_display_name())


class QTacticProjectSelectWdg(QtGui.QWidget, QTacticBasicInputWdg):
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

        # self.init_default_value()

        # if not self.init_default_value():
        #     self.autofill_by_parent()

    def autofill_by_parent(self):

        sobject = self.parent_sobject
        if not sobject:
            sobject = self.sobject

        if sobject:
            column = sobject.info.get(self.get_column())
            if column:
                for i, value in enumerate(self.tactic_widget.get_values()):
                    if column == value:
                        self.combo_box.setCurrentIndex(i)

    def init_default_value(self):

        display_values = self.tactic_widget.get_display_values()

        if display_values.get('labels'):
            default_value = display_values.get('labels')[0]

        else:
            default_value = None

        if default_value:
            for i, value in enumerate(self.tactic_widget.get_values()):
                if default_value == value:
                    self.combo_box.setCurrentIndex(i)
                    return True

    def get_data(self):

        codes = self.tactic_widget.get_values()
        index = self.combo_box.currentIndex()

        if not codes[index]:
            return ''
        else:
            return codes[index]

    def get_column(self):
        action_options = self.tactic_widget.get_action_options()
        column = action_options.get('column')
        if column:
            return column
        else:
            return self.tactic_widget.get_name()

    def create_combo_box(self):
        self.combo_box = QtGui.QComboBox()
        self.combo_box.setEditable(True)
        self.combo_box.setCurrentIndex(0)

    def add_items_to_combo_box(self):
        labels = self.tactic_widget.get_labels()
        for label in labels:
            self.combo_box.addItem(label)


class QTacticTaskStatusSelectWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()

        self.tactic_widget = tactic_widget
        self.parent_ui = parent
        self.parent_sobject = self.tactic_widget.get_parent_sobject()

        self.create_processes_combo_box()

        self.set_title(self.tactic_widget.get_title())
        self.fill_default_values()

        self.set_control_widget(self.statuses_combo_box)

    def get_data(self):
        if self.statuses_combo_box.currentIndex() not in [-1, 0]:
            return self.statuses_combo_box.currentText()

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):

        task_pipelines = self.tactic_widget.get_value('task_pipelines')
        info_dict = self.parent_ui.get_info_dict()
        current_process = None
        if info_dict:
            current_process = info_dict.get('process')

        if task_pipelines and self.parent_sobject and current_process:
            stype = self.parent_sobject.get_stype()
            parent_sobject_pipeline_code = self.parent_sobject.get_pipeline_code()
            workflow = stype.get_workflow()

            stype_current_pipeline = stype.get_pipeline()
            if stype_current_pipeline:
                current_pipeline = stype_current_pipeline.get(parent_sobject_pipeline_code)
                process_info = current_pipeline.get_process_info(current_process)
                if process_info:

                    task_pipeline_code = process_info.get('task_pipeline')

                    if task_pipeline_code:
                        task_pipeline = workflow.get_by_pipeline_code('sthpw/task', task_pipeline_code)
                    else:
                        process_type = process_info.get('type')
                        task_pipeline = workflow.get_by_process_node_type('sthpw/task', process_type)

                    if task_pipeline:
                        for process, value in task_pipeline.pipeline.items():
                            self.statuses_combo_box.add_item(process, hex_color=value.get('color'))

    def create_processes_combo_box(self):

        self.statuses_combo_box = Ui_coloredComboBox()
        self.statuses_combo_box.add_item('--{0}--'.format(self.tactic_widget.get_name()), hex_color='#303030')


class QTacticSubContextInputWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        self.create_text_edit()

        self.set_title(self.tactic_widget.get_title())
        self.fill_default_values()
        self.set_control_widget(self.text_edit)

    def get_data(self):
        if str(self.text_edit.text()) != str(self.tactic_widget.get_default_values()):
            return str(self.text_edit.text())

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):
        if self.tactic_widget.get_default_values():
            self.text_edit.setText(str(self.tactic_widget.get_default_values()))

    def create_text_edit(self):
        self.text_edit = QtGui.QLineEdit()


class QTacticProcessInputWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()

        self.tactic_widget = tactic_widget
        self.parent_ui = parent
        self.parent_sobject = self.tactic_widget.get_parent_sobject()

        self.create_processes_combo_box()

        self.set_title(self.tactic_widget.get_title())
        self.fill_default_values()

        self.set_control_widget(self.statuses_combo_box)

    def get_data(self):
        if self.statuses_combo_box.currentIndex() not in [-1, 0]:
            return self.statuses_combo_box.currentText()

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):

        pipeline_codes = self.tactic_widget.get_value('pipeline_codes')
        info_dict = self.parent_ui.get_info_dict()
        current_process = None
        if info_dict:
            current_process = info_dict.get('process')

        if pipeline_codes and self.parent_sobject and current_process:
            stype = self.parent_sobject.get_stype()
            parent_sobject_pipeline_code = self.parent_sobject.get_pipeline_code()

            stype_current_pipeline = stype.get_pipeline()
            if stype_current_pipeline:
                current_pipeline = stype_current_pipeline.get(parent_sobject_pipeline_code)

                if current_pipeline:
                    for process, value in current_pipeline.pipeline.items():
                        self.statuses_combo_box.add_item(process, hex_color=value.get('color'))

                    status_index = self.statuses_combo_box.findText(current_process)
                    if status_index != -1:
                        self.statuses_combo_box.setCurrentIndex(status_index)

    def create_processes_combo_box(self):

        self.statuses_combo_box = Ui_coloredComboBox()
        self.statuses_combo_box.add_item('--{0}--'.format(self.tactic_widget.get_name()), hex_color='#303030')


class QTacticPipelineInputWdg(QtGui.QWidget, QTacticBasicInputWdg):
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

        self.set_default_value()

    def set_default_value(self):

        default_label = self.tactic_widget.get_default_values()

        # in case we're editing
        current_label = self.tactic_widget.get_current_label()

        if current_label:
            default_label = current_label

        if default_label:
            for i, label in enumerate(self.tactic_widget.get_labels()):
                if label == default_label:
                    self.combo_box.setCurrentIndex(i)
                    return True

    def get_data(self):

        codes = self.tactic_widget.get_values()
        index = self.combo_box.currentIndex()
        if codes:
            if not codes[index]:
                return ''
            else:
                return codes[index]

    def get_column(self):
        action_options = self.tactic_widget.get_action_options()
        column = action_options.get('column')
        if column:
            return column
        else:
            return self.tactic_widget.get_name()

    def create_combo_box(self):
        self.combo_box = QtGui.QComboBox()
        self.combo_box.setEditable(True)
        self.combo_box.setCurrentIndex(0)

    def add_items_to_combo_box(self):
        labels = self.tactic_widget.get_labels()
        for label in labels:
            self.combo_box.addItem(label)
