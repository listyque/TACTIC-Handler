# file ui_drop_plate_classes.py

import os
from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtGui as Qt4Gui
from lib.side.Qt import QtCore

from lib.environment import env_mode
import lib.global_functions as gf
import lib.ui.checkin_out.ui_drop_plate as ui_drop_plate
import lib.ui.checkin_out.ui_drop_plate_config as ui_drop_plate_config

reload(ui_drop_plate)
reload(ui_drop_plate_config)


class Ui_matchingTemplateConfigWidget(QtGui.QDialog, ui_drop_plate_config.Ui_matchingTemplateConfig):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.current_templates_list = []

        self.setupUi(self)
        self.drop_plate_config_ui()

    def drop_plate_config_ui(self):
        self.setWindowTitle('Matching Template Config')

        self.fill_templates()

        self.templatesTreeWidget.resizeColumnToContents(0)
        self.templatesTreeWidget.resizeColumnToContents(1)
        self.templatesTreeWidget.resizeColumnToContents(2)
        self.templatesTreeWidget.resizeColumnToContents(3)

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
            (True, '$FILENAME.$LAYER.$EXT'),
            (True, '$FILENAME_$LAYER.$FRAME.$EXT'),
            (True, '$FILENAME.$LAYER.$FRAME.$EXT'),
            (True, '$FILENAME.$LAYER_$UV.$EXT'),
            (True, '$FILENAME.$LAYER.$FRAME_$UV.$EXT'),
            (True, '$FILENAME.$LAYER_$UV.$FRAME.$EXT'),
            (True, '$FILENAME.$LAYER_$UDIM.$EXT'),
            (True, '$FILENAME.$LAYER.$FRAME_$UDIM.$EXT'),
            (True, '$FILENAME.$LAYER_$UDIM.$FRAME.$EXT'),
            (False, '$FILENAME_$LAYER.$FRAME_$UDIM.$EXT'),
        ]

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
        return int(self.minFramesPaddingSpinBox.value())

    def get_templates_list(self):

        return self.current_templates_list


class Ui_dropPlateWidget(QtGui.QWidget, ui_drop_plate.Ui_dropPlate):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.tree_items = []

        self.setupUi(self)

        self.setAcceptDrops(True)
        self.dropTreeWidget.setDragDropMode(QtGui.QAbstractItemView.DragOnly)

        self.create_drop_plate_ui()
        self.create_config_widget()
        self.controls_actions()

    def create_drop_plate_ui(self):

        self.clearPushButton.setIcon(gf.get_icon('trash'))
        self.configPushButton.setIcon(gf.get_icon('cog'))

        self.setAcceptDrops(True)
        self.dropTreeWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

        if env_mode.get_mode() == 'standalone':
            self.fromDropListCheckBox.setHidden(True)
            sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
            self.setSizePolicy(sizePolicy)
            self.setMinimumWidth(300)

    def create_config_widget(self):
        self.config_widget = Ui_matchingTemplateConfigWidget(self)

    def controls_actions(self):

        self.clearPushButton.clicked.connect(self.clear_tree_widget)
        self.configPushButton.clicked.connect(self.config_widget.exec_)
        self.groupCheckinCheckBox.stateChanged.connect(self.enable_group_checkin)

        self.create_files_tree_context_menu()

    def enable_group_checkin(self, state):

        if state:
            self.dropTreeWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            self.keepFileNameCheckBox.setEnabled(False)
        else:
            self.dropTreeWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
            self.dropTreeWidget.clearSelection()
            self.keepFileNameCheckBox.setEnabled(True)

    def clear_tree_widget(self):

        self.dropTreeWidget.clear()
        self.fromDropListCheckBox.setChecked(False)
        self.tree_items = []

    def create_files_tree_context_menu(self):
        self.dropTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.dropTreeWidget.customContextMenuRequested.connect(self.open_menu)

    def open_menu(self):
        item = self.dropTreeWidget.currentItem()
        if item:
            menu = self.file_context_menu()
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

        menu = QtGui.QMenu()

        menu.addAction(open_file)
        menu.addAction(open_file_folder)
        menu.addAction(copy_path)
        menu.addAction(copy_abs_path)

        return menu

    def get_selected_items(self):
        if self.tree_items:
            selected_items = []
            for item in self.dropTreeWidget.selectedItems():
                index = item.data(0, QtCore.Qt.UserRole)
                for i, itm in enumerate(self.tree_items):
                    if i == index:
                        selected_items.append(itm)

            return selected_items

    def append_items_to_tree(self, items):
        if self.includeSubfoldersCheckBox.isChecked():
            dirs_and_files = gf.split_files_and_dirs(items)
            for dirs in dirs_and_files[0]:
                for path, subdirs, files in os.walk(dirs):
                    for name in files:
                        items.append(os.path.join(path, name))
                    for s_dir in subdirs:
                        items.append(os.path.join(path, s_dir))

        self.fromDropListCheckBox.setChecked(True)

        self.dropTreeWidget.clearSelection()

        if len(items) > 1:
            self.groupCheckinCheckBox.setChecked(True)
        if len(items) == 1:
            self.groupCheckinCheckBox.setChecked(False)

        match_template = gf.MatchTemplate(self.config_widget.get_templates_list(), padding=self.config_widget.get_min_padding())

        files_objects_dict = match_template.get_files_objects(items)

        icon_provider = QtGui.QFileIconProvider()

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

                if self.dropTreeWidget.topLevelItemCount() < 50:  # for performance reasons
                    self.dropTreeWidget.setItemSelected(tree_item, True)
                else:
                    self.dropTreeWidget.clearSelection()

                tree_item.setData(0, QtCore.Qt.UserRole, len(self.tree_items))
                self.tree_items.append(file_obj)

                if i % 10 == 0:
                    QtGui.QApplication.processEvents()

        self.dropTreeWidget.resizeColumnToContents(0)
        self.dropTreeWidget.resizeColumnToContents(1)
        self.dropTreeWidget.resizeColumnToContents(2)
        self.dropTreeWidget.resizeColumnToContents(3)
        self.dropTreeWidget.resizeColumnToContents(4)

        self.dropTreeWidget.sortByColumn(0, QtCore.Qt.AscendingOrder)

    def set_item_widget(self, item_widget):
        pass
        # self.item_widget = item_widget
        # if self.item_widget.type in ['snapshot', 'sobject', 'process']:
        #     checkin_mode = self.item_widget.get_checkin_mode_options()
        #     self.set_checkin_mode(checkin_mode)

    def get_keep_filename(self):

        return self.keepFileNameCheckBox.isChecked()

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'includeSubfoldersCheckBox': False,
                'keepFileNameCheckBox': False,
                'fromDropListCheckBox': False,
                'groupCheckinCheckBox': False,
                # 'checkinTypeComboBox': 0
            }

        self.includeSubfoldersCheckBox.setChecked(settings_dict['includeSubfoldersCheckBox'])
        self.keepFileNameCheckBox.setChecked(settings_dict['keepFileNameCheckBox'])
        self.fromDropListCheckBox.setChecked(settings_dict['fromDropListCheckBox'])
        self.groupCheckinCheckBox.setChecked(settings_dict['groupCheckinCheckBox'])
        # self.checkinTypeComboBox.setCurrentIndex(settings_dict['checkinTypeComboBox'])

    def get_settings_dict(self):

        settings_dict = {
            'includeSubfoldersCheckBox': int(self.includeSubfoldersCheckBox.isChecked()),
            'keepFileNameCheckBox': int(self.keepFileNameCheckBox.isChecked()),
            'fromDropListCheckBox': int(self.fromDropListCheckBox.isChecked()),
            'groupCheckinCheckBox': int(self.groupCheckinCheckBox.isChecked()),
            # 'checkinTypeComboBox': int(self.checkinTypeComboBox.currentIndex())

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
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(unicode(url.toLocalFile()))
            self.append_items_to_tree(links)
        else:
            event.ignore()
