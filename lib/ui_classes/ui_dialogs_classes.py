from lib.side.Qt import QtWidgets as QtGui
# from lib.side.Qt import QtCore

import lib.ui_classes.ui_misc_classes as ui_misc_classes

# import lib.tactic_classes as tc
import lib.global_functions as gf
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


class saveConfirmWidget(QtGui.QWidget):
    def __init__(self, item_widget, paths, repo, context, update_versionless, description, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.item_widget = item_widget
        self.paths = paths
        print self.paths, 'paths saveConfirmWidget'
        self.repo = repo
        self.context = context
        self.update_versionless = update_versionless
        self.description = description
        self.shown = False

    def create_ui(self):

        self.shown = True
        self.create_main_layout()

        self.create_info_label_widget()
        self.create_label_widget()

        self.create_checkboxes_widget()

        self.create_versionless_widget()
        self.create_versions_widget()

        self.create_description_widget()

        self.switch_versionless_label()

        self.controls_actions()

    def get_data_dict(self):

        data_dict = {
            'description': self.description_widget.get_description('plain'),
            'update_versionless': self.update_versionless_checkbox.isChecked(),
        }

        return data_dict

    def showEvent(self, event):
        if not self.shown:
            self.create_ui()

    def controls_actions(self):
        self.update_versionless_checkbox.stateChanged.connect(self.switch_versionless_label)

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def create_checkboxes_widget(self):
        self.update_versionless_checkbox = QtGui.QCheckBox('Update Versionless')
        if self.update_versionless:
            self.update_versionless_checkbox.setChecked(True)
        else:
            self.update_versionless_checkbox.setChecked(False)
        self.main_layout.addWidget(self.update_versionless_checkbox)

    def create_info_label_widget(self):
        self.info_label_widget = QtGui.QLabel()

        self.info_label_widget.setText(
            'Context: <b>{0}</b>; '
            'Repository: <span style="color:{2};"><b>{1}</b></span>; '.format(
                self.context,
                self.repo['value'][1],
                'rgb({},{},{})'.format(*self.repo['value'][2]),))

        self.main_layout.addWidget(self.info_label_widget)

    def create_label_widget(self):
        self.update_versionless_label = QtGui.QLabel()
        self.main_layout.addWidget(self.update_versionless_label)

    def switch_versionless_label_text(self):
        if self.update_versionless:
            self.update_versionless_label.setText('<p>Versionless files will be <span style="color:#00aa00;"><b>Updated</b></span></p>')
        else:
            self.update_versionless_label.setText('<p>Versionless files will <span style="color:#aa0000;"><b>not be</b></span> Updated</p>')

    def switch_versionless_label(self):

        if self.update_versionless_checkbox.isChecked():
            self.update_versionless = True
            self.collapse_wdg_vls.setVisible(True)
        else:
            self.update_versionless = False
            self.collapse_wdg_vls.setVisible(False)

        self.switch_versionless_label_text()

    def create_versionless_widget(self):

        self.collapse_wdg_vls = ui_misc_classes.Ui_collapsableWidget()
        layout_files = QtGui.QVBoxLayout()
        self.collapse_wdg_vls.setLayout(layout_files)
        self.collapse_wdg_vls.setText('Hide Versionless Files')
        self.collapse_wdg_vls.setCollapsedText('Show Versionless Files')
        self.collapse_wdg_vls.setCollapsed(True)

        # self.files_tree_widget = QtGui.QTreeWidget()
        self.treeWidget_vls = QtGui.QTreeWidget()
        self.treeWidget_vls.setAlternatingRowColors(True)
        self.treeWidget_vls.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.treeWidget_vls.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.treeWidget_vls.setRootIsDecorated(False)
        self.treeWidget_vls.headerItem().setText(0, "File")
        self.treeWidget_vls.headerItem().setText(1, "Path")
        self.treeWidget_vls.setStyleSheet('QTreeView::item {padding: 2px;}')
        for keys, values in self.paths:
            for i, fl in enumerate(values['versionless']['names']):
                full_path = gf.form_path(self.repo['value'][0] + '/' + values['versionless']['paths'][i])
                item = QtGui.QTreeWidgetItem()
                item.setText(0, ''.join(fl))
                item.setText(1, full_path)
                self.treeWidget_vls.addTopLevelItem(item)
            self.treeWidget_vls.setMinimumWidth(self.treeWidget_vls.columnWidth(0) + self.treeWidget_vls.columnWidth(1) + 150)
        self.treeWidget_vls.setMinimumHeight(250)
        self.treeWidget_vls.resizeColumnToContents(0)
        self.treeWidget_vls.resizeColumnToContents(1)

        layout_files.addWidget(self.treeWidget_vls)

        self.main_layout.addWidget(self.collapse_wdg_vls)

    def create_versions_widget(self):

        self.collapse_wdg_vers = ui_misc_classes.Ui_collapsableWidget()
        layout_files = QtGui.QVBoxLayout()
        self.collapse_wdg_vers.setLayout(layout_files)
        self.collapse_wdg_vers.setText('Hide Versions Files')
        self.collapse_wdg_vers.setCollapsedText('Show Versions Files')
        self.collapse_wdg_vers.setCollapsed(True)

        # self.files_tree_widget = QtGui.QTreeWidget()
        self.treeWidget_vers = QtGui.QTreeWidget()
        self.treeWidget_vers.setAlternatingRowColors(True)
        self.treeWidget_vers.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.treeWidget_vers.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.treeWidget_vers.setRootIsDecorated(False)
        self.treeWidget_vers.headerItem().setText(0, "File")
        self.treeWidget_vers.headerItem().setText(1, "Path")
        self.treeWidget_vers.setStyleSheet('QTreeView::item {padding: 2px;}')
        for keys, values in self.paths:
            for i, fl in enumerate(values['versioned']['names']):
                full_path = gf.form_path(self.repo['value'][0] + '/' + values['versioned']['paths'][i])
                item = QtGui.QTreeWidgetItem()
                item.setText(0, ''.join(fl))
                item.setText(1, full_path)
                self.treeWidget_vers.addTopLevelItem(item)
            self.treeWidget_vers.setMinimumWidth(self.treeWidget_vers.columnWidth(0) + self.treeWidget_vers.columnWidth(1) + 150)
        self.treeWidget_vers.setMinimumHeight(250)
        self.treeWidget_vers.resizeColumnToContents(0)
        self.treeWidget_vers.resizeColumnToContents(1)

        layout_files.addWidget(self.treeWidget_vers)

        self.main_layout.addWidget(self.collapse_wdg_vers)

    def create_description_widget(self):

        self.collapse_wdg_descr = ui_misc_classes.Ui_collapsableWidget()
        layout_files = QtGui.QVBoxLayout()
        self.collapse_wdg_descr.setLayout(layout_files)
        self.collapse_wdg_descr.setText('Hide Description')
        self.collapse_wdg_descr.setCollapsedText('Show Description')
        self.collapse_wdg_descr.setCollapsed(False)

        from lib.ui_classes.ui_checkin_out_classes import Ui_descriptionWidget

        self.description_widget = Ui_descriptionWidget(None, None, parent=self)
        self.description_widget.descriptionTextEdit.setViewportMargins(0, 20, 0, 0)

        self.description_widget.setMinimumHeight(200)
        self.description_widget.setMinimumWidth(400)

        self.description_widget.set_description(self.description)

        layout_files.addWidget(self.description_widget)

        self.main_layout.addWidget(self.collapse_wdg_descr)
