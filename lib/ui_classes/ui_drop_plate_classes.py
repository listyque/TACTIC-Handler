# file ui_drop_plate_classes.py

# import PySide.QtGui as QtGui
# import PySide.QtCore as QtCore
from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore

from lib.environment import env_mode
import lib.global_functions as gf
import lib.ui.checkin_out.ui_drop_plate as ui_drop_plate
# TODO create sequences parsing
# import lib.side.pyseq as pyseq

reload(ui_drop_plate)


# seqs = pyseq.get_sequences('//renderserver/Project/projectName/scenes/ep29/ep29sc27/compose/sequence/tif/v1')
# print(seqs)


class Ui_dropPlateWidget(QtGui.QWidget, ui_drop_plate.Ui_dropPlate):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.setAcceptDrops(True)

        self.create_drop_plate_ui()
        self.controls_actions()

    def create_drop_plate_ui(self):

        self.clearPushButton.setIcon(gf.get_icon('eraser'))

        self.setAcceptDrops(True)
        self.dropTreeWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

        if env_mode.get_mode() == 'standalone':
            self.fromDropListCheckBox.setHidden(True)
            sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
            self.setSizePolicy(sizePolicy)
            self.setMinimumWidth(300)

    def controls_actions(self):

        self.clearPushButton.clicked.connect(self.clear_tree_widget)
        self.groupCheckinCheckBox.stateChanged.connect(self.enable_group_checkin)

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

    def append_items_to_tree(self, items):

        # file_dir_tuple = split_files_and_dirs(items)
        # print(file_dir_tuple)
        self.fromDropListCheckBox.setChecked(True)

        self.dropTreeWidget.clearSelection()

        if len(items) > 1:
            self.groupCheckinCheckBox.setChecked(True)
        if len(items) == 1:
            self.groupCheckinCheckBox.setChecked(False)

        extract_ext = gf.extract_extension

        for item in items:
            ext = extract_ext(item)
            tree_item = QtGui.QTreeWidgetItem()
            tree_item.setText(0, gf.extract_filename(item))
            tree_item.setData(0, QtCore.Qt.UserRole, gf.extract_filename(item, True))
            tree_item.setText(1, ext[1])
            tree_item.setData(1, QtCore.Qt.UserRole, ext[0])
            tree_item.setText(2, ext[2])
            tree_item.setText(3, gf.extract_dirname(item))
            self.dropTreeWidget.addTopLevelItem(tree_item)
            self.dropTreeWidget.setItemSelected(tree_item, True)

        self.dropTreeWidget.resizeColumnToContents(0)
        self.dropTreeWidget.resizeColumnToContents(1)
        self.dropTreeWidget.resizeColumnToContents(2)
        self.dropTreeWidget.resizeColumnToContents(3)

    def set_item_widget(self, item_widget):
        self.item_widget = item_widget
        if self.item_widget.type in ['snapshot', 'sobject', 'process']:
            checkin_mode = self.item_widget.get_checkin_mode_options()
            self.set_checkin_mode(checkin_mode)

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

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'includeSubfoldersCheckBox': False,
                'keepFileNameCheckBox': False,
                'fromDropListCheckBox': False,
                'groupCheckinCheckBox': False,
                'checkinTypeComboBox': 0
            }

        self.includeSubfoldersCheckBox.setChecked(settings_dict['includeSubfoldersCheckBox'])
        self.keepFileNameCheckBox.setChecked(settings_dict['keepFileNameCheckBox'])
        self.fromDropListCheckBox.setChecked(settings_dict['fromDropListCheckBox'])
        self.groupCheckinCheckBox.setChecked(settings_dict['groupCheckinCheckBox'])
        self.checkinTypeComboBox.setCurrentIndex(settings_dict['checkinTypeComboBox'])

    def get_settings_dict(self):

        settings_dict = {
            'includeSubfoldersCheckBox': int(self.includeSubfoldersCheckBox.isChecked()),
            'keepFileNameCheckBox': int(self.keepFileNameCheckBox.isChecked()),
            'fromDropListCheckBox': int(self.fromDropListCheckBox.isChecked()),
            'groupCheckinCheckBox': int(self.groupCheckinCheckBox.isChecked()),
            'checkinTypeComboBox': int(self.checkinTypeComboBox.currentIndex())

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
