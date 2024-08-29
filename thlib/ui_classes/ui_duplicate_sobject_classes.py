from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore
import thlib.tactic_classes as tc
import thlib.global_functions as gf
from thlib.environment import env_inst

from thlib.ui_classes.ui_custom_qwidgets import Ui_collapsableWidget


class duplicateSobjectWidget(QtGui.QWidget):
    def __init__(self, sobjects, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.sobjects = sobjects
        self.dependencies = None

        self.get_dependencies()

        self.shown = False

    def create_ui(self):
        self.shown = True

        self.create_main_layout()

        self.create_new_name_widget()

        self.create_dependency_widget()

    def get_dependencies(self):
        if len(self.sobjects) > 1:
            search_keys = []
            for sobject in self.sobjects:
                search_keys.append(sobject.get_search_key())

            self.dependencies = tc.get_all_dependency(search_keys)
        else:
            self.dependencies = tc.get_all_dependency([self.sobjects[0].get_search_key()])

    def get_current_search_type(self):
        return self.sobjects[0].get_stype()

    def get_data_dict(self):

        data_dict = {
            'related_search_type': self.get_confirmed_search_types(),
            'new_name': self.get_new_name(),
        }

        return data_dict

    def showEvent(self, event):
        if not self.shown:
            self.create_ui()

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def create_new_name_widget(self):

        if len(self.sobjects) > 1:
            # search_keys = []
            for sobject in self.sobjects:
                print(sobject)
                # search_keys.append(sobject.get_search_key())
        else:
            print(self.sobjects[0])

            self.new_name_layout = QtGui.QHBoxLayout()
            self.label = QtGui.QLabel('New Name: ')
            self.new_name_edit = QtGui.QLineEdit()

            self.new_name_layout.addWidget(self.label)
            self.new_name_layout.addWidget(self.new_name_edit)

            self.main_layout.addLayout(self.new_name_layout, 0, 0)

            self.new_name_edit.setText(u'{0}_new'.format(self.sobjects[0].get_value('name')))

    def create_dependency_widget(self):
        pos = 1

        check_list = []

        self.check_boxes_list = []

        parent_search_type = self.get_current_search_type()
        project = parent_search_type.get_project()
        schema = parent_search_type.get_schema()

        for search_type, sobjects in self.dependencies.items():

            if search_type and search_type.startswith('sthpw'):
                stype = env_inst.get_stype_by_code(search_type)
            else:
                stype = env_inst.get_stype_by_code(search_type, project_code=project.get_code())

            if stype:
                if schema:
                    child = schema.get_child(stype.get_code(), parent_search_type.get_code())

                    if child:
                        relationship = child.get('relationship')
                        if relationship == 'instance':
                            instance_type = child.get('instance_type')
                            check_list.append(instance_type)

            # Filtering if the sobject points to self as dependency
            for sobject in self.sobjects:
                for dep_skey in list(sobjects.keys()):
                    if sobject.get_search_key() == dep_skey:
                        sobjects.pop(dep_skey)

            if len(sobjects) > 0:
                pos += 1
                layout = QtGui.QHBoxLayout()

                duplicate_check_box = QtGui.QCheckBox()
                duplicate_check_box.setObjectName(search_type)
                if search_type in check_list:
                    duplicate_check_box.setChecked(True)
                layout.addWidget(duplicate_check_box)

                self.check_boxes_list.append(duplicate_check_box)

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

    def get_confirmed_search_types(self):

        search_types = []

        for check_box in self.check_boxes_list:
            if check_box.isChecked():
                search_types.append(check_box.objectName())

        # if not search_types:
        #     search_types.append(self.sobjects[0].get_plain_search_type())

        return search_types

    def get_new_name(self):

        return self.new_name_edit.text()


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
