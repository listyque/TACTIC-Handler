from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore
import thlib.tactic_classes as tc
import thlib.global_functions as gf

from thlib.ui_classes.ui_custom_qwidgets import Ui_collapsableWidget


class deleteSobjectWidget(QtGui.QWidget):
    def __init__(self, sobjects, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.sobjects = sobjects
        self.dependencies = None

        self.get_dependencies()

        self.shown = False

    def create_ui(self):
        self.shown = True

        self.create_main_layout()

        self.create_dependency_widget()

    def get_dependencies(self):
        if len(self.sobjects) > 1:
            search_keys = []
            for sobject in self.sobjects:
                search_keys.append(sobject.get_search_key())

            self.dependencies = tc.get_all_dependency(search_keys)
        else:
            self.dependencies = tc.get_all_dependency([self.sobjects[0].get_search_key()])

    def get_data_dict(self):

        data_dict = {
            'search_types': self.get_confirmed_to_delete_search_types(),
        }

        return data_dict

    def showEvent(self, event):
        if not self.shown:
            self.create_ui()

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def create_dependency_widget(self):
        pos = 0

        check_list = ['sthpw/snapshot', 'sthpw/file', 'sthpw/note', 'sthpw/task', 'sthpw/status_log']

        self.check_boxes_list = []

        for search_type, sobjects in self.dependencies.items():

            # Filtering if the sobject points to self as dependency
            for sobject in self.sobjects:
                for dep_skey in sobjects.keys():
                    if sobject.get_search_key() == dep_skey:
                        sobjects.pop(dep_skey)

            if len(sobjects) > 0:
                pos += 1
                layout = QtGui.QHBoxLayout()

                deleting_check_box = QtGui.QCheckBox()
                deleting_check_box.setObjectName(search_type)
                if search_type in check_list:
                    deleting_check_box.setChecked(True)
                layout.addWidget(deleting_check_box)

                self.check_boxes_list.append(deleting_check_box)

                collapse_wdg_files = Ui_collapsableWidget(state=True)
                layout_files = QtGui.QVBoxLayout()

                collapse_wdg_files.setLayout(layout_files)
                collapse_wdg_files.setText(u'Hide {0} | {1}'.format(search_type, len(sobjects)))
                collapse_wdg_files.setCollapsedText(u'Show {0} | {1}'.format(search_type, len(sobjects)))

                files_tree_widget = Ui_dependencyExpandWidget(sobjects=sobjects)
                files_tree_widget.setMinimumSize(600, 300)

                layout_files.addWidget(files_tree_widget)

                layout.addWidget(collapse_wdg_files)

                self.main_layout.addLayout(layout, pos, 0)

    def get_confirmed_to_delete_search_types(self):

        search_types = []

        for check_box in self.check_boxes_list:
            if check_box.isChecked():
                search_types.append(check_box.objectName())

        if not search_types:
            search_types.append(self.sobjects[0].get_plain_search_type())

        return search_types


class Ui_dependencyExpandWidget(QtGui.QWidget):
    def __init__(self, sobjects, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.sobjects = sobjects
        self.shown = False

    def create_ui(self):
        self.shown = True

        self.create_main_layout()

        self.create_tree_widget()

        self.fill_tree_widget()

    def create_main_layout(self):
        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

    def create_tree_widget(self):
        self.tree_widget = QtGui.QTreeWidget()
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.tree_widget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.tree_widget.setRootIsDecorated(False)
        self.tree_widget.headerItem().setText(0, "Title")
        self.tree_widget.headerItem().setText(1, "Search Key")
        self.tree_widget.setStyleSheet(gf.get_qtreeview_style())
        self.tree_widget.setTextElideMode(QtCore.Qt.ElideLeft)

        self.main_layout.addWidget(self.tree_widget)

    def fill_tree_widget(self):
        self.tree_widget.clear()

        for sobject in self.sobjects.values():
            item = QtGui.QTreeWidgetItem()
            item.setText(0, sobject.get_title())
            item.setText(1, sobject.get_search_key())
            self.tree_widget.addTopLevelItem(item)

        self.tree_widget.resizeColumnToContents(0)

    def showEvent(self, event):
        if not self.shown:
            self.create_ui()
