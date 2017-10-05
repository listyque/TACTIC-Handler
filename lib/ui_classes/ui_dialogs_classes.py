from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore

import lib.ui_classes.ui_misc_classes as ui_misc_classes

# import lib.tactic_classes as tc
# import lib.global_functions as gf
# from lib.environment import env_inst


class deleteSobjectWidget(QtGui.QWidget):
    def __init__(self, sobject, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.sobject = sobject
        self.shown = False

    def create_ui(self):
        print self.sobject, 'creating delete widget'
        self.shown = True
        self.create_main_layout()
        self.create_checkboxes_widget()
        self.create_files_dependencies_widget()
        self.create_snapshots_dependencies_widget()
        self.create_tasks_dependencies_widget()
        self.create_notes_dependencies_widget()

        self.controls_actions()

    def get_data_dict(self):

        data_dict = {
            'del_files': self.delete_files_checkbox.isChecked(),
            'del_snapshots': self.delete_snapshot_checkbox.isChecked(),
            'del_tasks': self.delete_tasks_checkbox.isChecked(),
            'del_notes': self.delete_notes_checkbox.isChecked(),
        }

        return data_dict

    def showEvent(self, event):
        if not self.shown:
            self.create_ui()

    def controls_actions(self):
        pass

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def create_checkboxes_widget(self):
        self.delete_files_checkbox = QtGui.QCheckBox('Delete files')
        self.delete_files_checkbox.setChecked(True)
        self.main_layout.addWidget(self.delete_files_checkbox)

        self.delete_snapshot_checkbox = QtGui.QCheckBox('Delete snapshots')
        self.delete_snapshot_checkbox.setChecked(True)
        self.main_layout.addWidget(self.delete_snapshot_checkbox)

        self.delete_tasks_checkbox = QtGui.QCheckBox('Delete tasks')
        self.delete_tasks_checkbox.setChecked(True)
        self.main_layout.addWidget(self.delete_tasks_checkbox)

        self.delete_notes_checkbox = QtGui.QCheckBox('Delete notes')
        self.delete_notes_checkbox.setChecked(True)
        self.main_layout.addWidget(self.delete_notes_checkbox)

    def create_files_dependencies_widget(self):

        collapse_wdg_files = ui_misc_classes.Ui_collapsableWidget()
        layout_files = QtGui.QVBoxLayout()
        collapse_wdg_files.setLayout(layout_files)
        collapse_wdg_files.setText('Hide Files Dependencies')
        collapse_wdg_files.setCollapsedText('Show Files Dependencies')
        collapse_wdg_files.setCollapsed(True)

        self.files_tree_widget = QtGui.QTreeWidget()

        layout_files.addWidget(self.files_tree_widget)

        self.main_layout.addWidget(collapse_wdg_files)

    def create_snapshots_dependencies_widget(self):

        collapse_wdg_snapshots = ui_misc_classes.Ui_collapsableWidget()
        layout_files = QtGui.QVBoxLayout()
        collapse_wdg_snapshots.setLayout(layout_files)
        collapse_wdg_snapshots.setText('Hide Snapshots Dependencies')
        collapse_wdg_snapshots.setCollapsedText('Show Snapshots Dependencies')
        collapse_wdg_snapshots.setCollapsed(True)

        self.files_tree_widget = QtGui.QTreeWidget()

        layout_files.addWidget(self.files_tree_widget)

        self.main_layout.addWidget(collapse_wdg_snapshots)

    def create_tasks_dependencies_widget(self):

        collapse_wdg_tasks = ui_misc_classes.Ui_collapsableWidget()
        layout_files = QtGui.QVBoxLayout()
        collapse_wdg_tasks.setLayout(layout_files)
        collapse_wdg_tasks.setText('Hide Tasks Dependencies')
        collapse_wdg_tasks.setCollapsedText('Show Tasks Dependencies')
        collapse_wdg_tasks.setCollapsed(True)

        self.files_tree_widget = QtGui.QTreeWidget()

        layout_files.addWidget(self.files_tree_widget)

        self.main_layout.addWidget(collapse_wdg_tasks)

    def create_notes_dependencies_widget(self):

        collapse_wdg_notes = ui_misc_classes.Ui_collapsableWidget()
        layout_files = QtGui.QVBoxLayout()
        collapse_wdg_notes.setLayout(layout_files)
        collapse_wdg_notes.setText('Hide Notes Dependencies')
        collapse_wdg_notes.setCollapsedText('Show Notes Dependencies')
        collapse_wdg_notes.setCollapsed(True)

        self.files_tree_widget = QtGui.QTreeWidget()

        layout_files.addWidget(self.files_tree_widget)

        self.main_layout.addWidget(collapse_wdg_notes)
