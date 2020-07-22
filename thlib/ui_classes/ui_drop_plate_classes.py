# file ui_drop_plate_classes.py

import os
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

from thlib.environment import env_mode, env_inst, env_write_config, env_read_config
import thlib.global_functions as gf
import thlib.ui.checkin_out.ui_drop_plate as ui_drop_plate
import thlib.ui.checkin_out.ui_drop_plate_config as ui_drop_plate_config
from thlib.ui_classes.ui_custom_qwidgets import Ui_horizontalCollapsableWidget

#reload(ui_drop_plate)
#reload(ui_drop_plate_config)


class Ui_matchingTemplateConfigWidget(QtGui.QDialog, ui_drop_plate_config.Ui_matchingTemplateConfig):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.current_templates_list = []

        self.setupUi(self)
        self.create_ui()

    def create_ui(self):
        self.setWindowTitle('Matching Template Config')

        self.fill_templates()

        self.templatesTreeWidget.resizeColumnToContents(0)
        self.templatesTreeWidget.resizeColumnToContents(1)
        self.templatesTreeWidget.resizeColumnToContents(2)
        self.templatesTreeWidget.resizeColumnToContents(3)
        self.create_drop_plate_config_widget()
        
        self.readSettings()

    def create_drop_plate_config_widget(self):

        from thlib.ui_classes.ui_conf_classes import Ui_checkinOptionsPageWidget

        self.drop_plate_config_widget = Ui_checkinOptionsPageWidget(self)

        self.drop_plate_config_widget.snapshotsSavingOptionsGroupBox.setHidden(True)
        self.drop_plate_config_widget.checkinMiscOptionsGroupBox.setHidden(True)
        self.drop_plate_config_widget.defaultRepoPathsGroupBox.setHidden(True)
        self.drop_plate_config_widget.customRepoPathsGroupBox.setHidden(True)

        self.configGridLayout.addWidget(self.drop_plate_config_widget)
        self.configGridLayout.setContentsMargins(0, 0, 0, 9)

    def fill_templates(self):

        templates = [
            (True, '$FILENAME'),
            (True, '$FILENAME.$EXT'),
            (True, '$FILENAME.$FRAME.$EXT'),
            (True, '$FILENAME_$UDIM.$EXT'),
            (True, '$FILENAME_$UV.$EXT'),
            (True, '$FILENAME.$FRAME_$UDIM.$EXT'),
            (True, '$FILENAME.$FRAME_$UV.$EXT'),
            (True, '$FILENAME_$UV.$FRAME.$EXT'),
            (False, '$FILENAME_$LAYER.$EXT'),
            (False, '$FILENAME.$LAYER.$EXT'),
            (False, '$FILENAME_$LAYER.$FRAME.$EXT'),
            (False, '$FILENAME.$LAYER.$FRAME.$EXT'),
            (False, '$FILENAME.$LAYER_$UV.$EXT'),
            (False, '$FILENAME.$LAYER.$FRAME_$UV.$EXT'),
            (False, '$FILENAME.$LAYER_$UV.$FRAME.$EXT'),
            (False, '$FILENAME.$LAYER_$UDIM.$EXT'),
            (False, '$FILENAME.$LAYER.$FRAME_$UDIM.$EXT'),
            (False, '$FILENAME.$LAYER_$UDIM.$FRAME.$EXT'),
            (False, '$FILENAME_$LAYER.$FRAME_$UDIM.$EXT'),
        ]
        # templates = [
        #     (True, '$FILENAME'),
        #     (True, '$FILENAME.$EXT'),
        #     (True, '$FILENAMEFrame$FRAME.$EXT'),
        # ]

        for enabled, template in templates:

            tree_item = QtGui.QTreeWidgetItem()
            if enabled:
                tree_item.setCheckState(0, QtCore.Qt.Checked)
                self.current_templates_list.append(template)
            else:
                tree_item.setCheckState(0, QtCore.Qt.Unchecked)
            tree_item.setText(1, template)
            match_template = gf.MatchTemplate([template], padding=self.get_min_padding())
            tree_item.setText(2, match_template.get_preview_string())
            tree_item.setText(3, match_template.get_type_string())

            if template in ['$FILENAME', '$FILENAME.$EXT']:
                tree_item.setDisabled(True)

            self.templatesTreeWidget.addTopLevelItem(tree_item)

    def get_min_padding(self):
        return 3
        # return int(self.minFramesPaddingSpinBox.value())

    def get_templates_list(self):

        return self.current_templates_list
    
    def set_settings_from_dict(self, settings_dict=None):
        if settings_dict:
            self.move(settings_dict['pos'][0], settings_dict['pos'][1])
            self.resize(settings_dict['size'][0], settings_dict['size'][1])

    def get_settings_dict(self):
        settings_dict = dict()
        settings_dict['pos'] = self.pos().toTuple()
        settings_dict['size'] = self.size().toTuple()

        return settings_dict
    
    def readSettings(self):

        self.set_settings_from_dict(env_read_config(filename='ui_drop_plate', unique_id='ui_main', long_abs_path=True))

    def writeSettings(self):

        env_write_config(self.get_settings_dict(), filename='ui_drop_plate', unique_id='ui_main', long_abs_path=True)

    def hideEvent(self, event):
        self.writeSettings()
        event.accept()


class Ui_dropPlateWidget(QtGui.QWidget, ui_drop_plate.Ui_dropPlate):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.tree_items = []

        self.setupUi(self)

        self.setAcceptDrops(True)

        self.create_ui()

        self.create_config_widget()
        self.controls_actions()

    def threads_fill_items(self, kwargs, exec_after_added=None):

        worker = env_inst.local_pool.add_task(self.get_files_objects, kwargs)

        worker.result.connect(self.append_items_to_tree)
        if exec_after_added:
            worker.finished.connect(exec_after_added)
        worker.error.connect(gf.error_handle)
        worker.start()

    def create_ui(self):

        self.clearPushButton.setIcon(gf.get_icon('trash'))
        self.configPushButton.setIcon(gf.get_icon('settings', icons_set='mdi'))
        self.create_progress_bar_widget()

        self.create_collapsable_toolbar()

        self.setAcceptDrops(True)

        if env_mode.get_mode() == 'standalone':
            sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
            self.setSizePolicy(sizePolicy)
            self.setMinimumWidth(300)

        self.move_controls_to_collapsable_toolbar()

        self.customize_ui()

    def customize_ui(self):
        self.dropTreeWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.dropTreeWidget.setDragDropMode(QtGui.QAbstractItemView.DragOnly)
        self.dropTreeWidget.setStyleSheet(gf.get_qtreeview_style())

    def create_progress_bar_widget(self):
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMaximum(100)
        self.progressBarLayout.addWidget(self.progressBar)
        self.progressBar.setTextVisible(True)
        self.progressBar.setVisible(False)

    def create_config_widget(self):
        self.config_widget = Ui_matchingTemplateConfigWidget(self)

    def create_collapsable_toolbar(self):
        self.collapsable_toolbar = Ui_horizontalCollapsableWidget()
        self.collapsable_toolbar.setText('Quick Config')

        self.buttons_layout = QtGui.QHBoxLayout()
        self.buttons_layout.setSpacing(0)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.collapsable_toolbar.setLayout(self.buttons_layout)
        self.collapsable_toolbar.setCollapsed(True)

        self.expandingLayout.addWidget(self.collapsable_toolbar)

    def add_widget_to_collapsable_toolbar(self, widget):
        self.buttons_layout.addWidget(widget)

    def move_controls_to_collapsable_toolbar(self):
        self.add_widget_to_collapsable_toolbar(self.groupCheckinCheckBox)
        self.add_widget_to_collapsable_toolbar(self.keepFileNameCheckBox)
        self.add_widget_to_collapsable_toolbar(self.includeSubfoldersCheckBox)
        self.collapsable_toolbar.setCollapsed(False)

    def controls_actions(self):

        self.clearPushButton.clicked.connect(self.clear_tree_widget)
        self.configPushButton.clicked.connect(self.config_widget.exec_)
        # self.groupCheckinCheckBox.stateChanged.connect(self.enable_group_checkin)

        self.create_files_tree_context_menu()

    def clear_tree_widget(self):

        self.dropTreeWidget.clear()
        self.tree_items = []

    def create_files_tree_context_menu(self):
        self.dropTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.dropTreeWidget.customContextMenuRequested.connect(self.open_menu)

    def open_menu(self):
        item = self.dropTreeWidget.selectedIndexes()
        if item:
            menu = self.file_context_menu()
            if menu:
                menu.exec_(Qt4Gui.QCursor.pos())
        else:
            menu = self.drop_plate_context_menu()
            if menu:
                menu.exec_(Qt4Gui.QCursor.pos())

    @gf.catch_error
    def open_file_from_tree(self):
        item = self.get_selected_items()
        for it in item:
            it.open_file()

    @gf.catch_error
    def open_folder_from_tree(self):
        item = self.get_selected_items()
        for it in item:
            it.open_folder()

    @gf.catch_error
    def copy_path_from_tree(self):
        item = self.get_selected_items()
        clipboard = QtGui.QApplication.instance().clipboard()
        files_list = set()
        for it in item:
            files_list.add(it.get_file_path())
        clipboard.setText('\n'.join(files_list))

    @gf.catch_error
    def copy_abs_path_from_tree(self):
        item = self.get_selected_items()
        clipboard = QtGui.QApplication.instance().clipboard()
        files_list = []
        for it in item:
            files_list.extend(it.get_all_files_list())
        clipboard.setText('\n'.join(files_list))

    def file_context_menu(self):
        open_file = QtGui.QAction('Open File', self.dropTreeWidget)
        open_file.setIcon(gf.get_icon('folder'))
        open_file.triggered.connect(self.open_file_from_tree)

        open_file_folder = QtGui.QAction('Show Folder', self.dropTreeWidget)
        open_file_folder.setIcon(gf.get_icon('folder-open'))
        open_file_folder.triggered.connect(self.open_folder_from_tree)

        copy_path = QtGui.QAction("Copy File Path", self.dropTreeWidget)
        copy_path.setIcon(gf.get_icon('copy'))
        copy_path.triggered.connect(self.copy_path_from_tree)

        copy_abs_path = QtGui.QAction("Copy Absolute File Path", self.dropTreeWidget)
        copy_abs_path.setIcon(gf.get_icon('copy'))
        copy_abs_path.triggered.connect(self.copy_abs_path_from_tree)

        add_file = QtGui.QAction('Add More Files', self.dropTreeWidget)
        add_file.setIcon(gf.get_icon('folder-open'))
        add_file.triggered.connect(self.add_files_from_menu)

        menu = QtGui.QMenu()

        menu.addAction(open_file)
        menu.addAction(open_file_folder)
        menu.addAction(copy_path)
        menu.addAction(copy_abs_path)
        menu.addAction(add_file)

        return menu

    def drop_plate_context_menu(self):
        add_file = QtGui.QAction('Add Files', self.dropTreeWidget)
        add_file.setIcon(gf.get_icon('folder-open'))
        add_file.triggered.connect(self.add_files_from_menu)

        paste_from_clipboard = QtGui.QAction('Paste From Clipboard', self.dropTreeWidget)
        paste_from_clipboard.setIcon(gf.get_icon('folder-open'))
        paste_from_clipboard.triggered.connect(self.add_files_from_clipboard)

        menu = QtGui.QMenu()

        menu.addAction(add_file)
        menu.addAction(paste_from_clipboard)

        return menu

    def add_files_from_menu(self, exec_after_added=None):

        options = QtGui.QFileDialog.Options()
        options |= QtGui.QFileDialog.DontUseNativeDialog
        files_names, filter = QtGui.QFileDialog.getOpenFileNames(self, 'Adding files to Drop Pate',
                                                              '',
                                                              'All Files (*.*);;',
                                                              '', options)

        if files_names:
            self.threads_fill_items(files_names, exec_after_added)
            # files_objects = self.get_files_objects(files_names)
            # self.append_items_to_tree(files_objects)
            # if exec_after_added:
            #     exec_after_added(files_objects)

    def add_files_from_clipboard(self, exec_after_added=None):
        clipboard = QtGui.QApplication.clipboard()
        files_names = clipboard.text()

        if files_names:
            files_names = set(files_names.split('\n'))
            self.threads_fill_items(files_names, exec_after_added)

    def get_selected_items(self):
        selected_items = []

        if self.tree_items:

            for item in self.dropTreeWidget.selectedItems():
                # index = item.data(0, QtCore.Qt.UserRole)
                file_object = item.data(1, QtCore.Qt.UserRole)
                # print file_object
                # for i, itm in enumerate(self.tree_items):
                #     print itm, i
                #     if i == index:
                #         selected_items.append(itm)
                #         break
                selected_items.append(file_object)

        return selected_items

    def get_files_objects(self, items):
        if self.includeSubfoldersCheckBox.isChecked():

            dirs_and_files = gf.split_files_and_dirs(items)

            for dirs in dirs_and_files[0]:
                for path, subdirs, files in os.walk(dirs):
                    for name in files:
                        items.append(os.path.join(path, name))
                    for s_dir in subdirs:
                        items.append(os.path.join(path, s_dir))

        match_template = gf.MatchTemplate(self.config_widget.get_templates_list(), padding=self.config_widget.get_min_padding())

        return match_template.get_files_objects(items)

    def remove_selected_items(self):
        if self.tree_items:
            for item in self.dropTreeWidget.selectedItems():
                index = item.data(0, QtCore.Qt.UserRole)
                for i, itm in enumerate(self.tree_items):
                    if i == index:
                        self.tree_items.pop(index)

                item_index = self.dropTreeWidget.indexFromItem(item)
                self.dropTreeWidget.takeTopLevelItem(item_index.row())

    def append_items_to_tree(self, files_objects_dict):
        self.dropTreeWidget.clearSelection()

        icon_provider = QtGui.QFileIconProvider()

        self.progressBar.setVisible(True)

        for item_type, item in files_objects_dict.items():

            for i, file_obj in enumerate(item):
                tree_item = QtGui.QTreeWidgetItem()
                tree_item.setText(0, file_obj.get_pretty_file_name())
                sequence_info_string = []
                frameranges = file_obj.get_sequence_frameranges_string('[]')
                tiles_count = file_obj.get_tiles_count()
                layer = file_obj.get_layer()
                if frameranges:
                    sequence_info_string.append(frameranges)
                if tiles_count:
                    sequence_info_string.append('{0} Tile(s)'.format(tiles_count))
                if layer:
                    sequence_info_string.append(layer)
                tree_item.setText(1, ' / '.join(sequence_info_string))
                tree_item.setText(2, file_obj.get_base_file_type_pretty_name())
                tree_item.setText(3, file_obj.get_base_file_type())
                tree_item.setText(4, file_obj.get_file_path())

                file_icon = icon_provider.icon(file_obj.get_all_files_list(True))
                tree_item.setIcon(0, file_icon)

                self.dropTreeWidget.addTopLevelItem(tree_item)

                # TODO fix this (we need to select all)
                # if self.dropTreeWidget.topLevelItemCount() < 50:  # for performance reasons
                self.dropTreeWidget.setItemSelected(tree_item, True)
                # else:
                #     self.dropTreeWidget.clearSelection()

                tree_item.setData(0, QtCore.Qt.UserRole, len(self.tree_items))
                tree_item.setData(1, QtCore.Qt.UserRole, file_obj)
                self.tree_items.append(file_obj)

                # if i+1 % 50 == 0:
                #     QtGui.QApplication.processEvents()

                self.progressBar.setValue(int(i+1 * 100 / len(item)))

        self.progressBar.setValue(100)
        self.dropTreeWidget.resizeColumnToContents(0)
        self.dropTreeWidget.resizeColumnToContents(1)
        self.dropTreeWidget.resizeColumnToContents(2)
        self.dropTreeWidget.resizeColumnToContents(3)
        self.dropTreeWidget.resizeColumnToContents(4)

        # self.dropTreeWidget.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.progressBar.setVisible(False)

    def get_keep_filename(self):

        return self.keepFileNameCheckBox.isChecked()

    def set_settings_from_dict(self, settings_dict=None):

        ref_settings_dict = {
            'includeSubfoldersCheckBox': False,
            'keepFileNameCheckBox': False,
            'groupCheckinCheckBox': False,
        }

        settings = gf.check_config(ref_settings_dict, settings_dict)

        self.includeSubfoldersCheckBox.setChecked(settings['includeSubfoldersCheckBox'])
        self.keepFileNameCheckBox.setChecked(settings['keepFileNameCheckBox'])
        self.groupCheckinCheckBox.setChecked(settings['groupCheckinCheckBox'])

    def get_settings_dict(self):

        settings_dict = {
            'includeSubfoldersCheckBox': int(self.includeSubfoldersCheckBox.isChecked()),
            'keepFileNameCheckBox': int(self.keepFileNameCheckBox.isChecked()),
            'groupCheckinCheckBox': int(self.groupCheckinCheckBox.isChecked()),

        }

        return settings_dict

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

        # print event.mimeData()
        # print event.mimeData().text()
        # print event.mimeData().urls()

        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(url.toLocalFile())
            self.threads_fill_items(links)
        else:
            event.ignore()
