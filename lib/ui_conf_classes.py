# ui_conf_classes.py
# Configuration window classes

import copy
import collections
import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import environment as env
import lib.ui.ui_conf as ui_conf
import tactic_classes as tc

if env.Mode().get == 'maya':
    # import ui_maya_dock
    import maya.cmds as cmds

reload(ui_conf)


class Ui_configuration_dialogWidget(QtGui.QDialog, ui_conf.Ui_configuration_dialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        self.first_run = False

        if env.Env().get_first_run():
            env.Env().get_default_dirs()
            self.first_run = True

        self.custom_repo_item = collections.OrderedDict(env.Env().rep_dirs['custom_asset_dir'])

        self.current_project = env.Env().get_project()
        self.current_namespace = env.Env().get_namespace()

        self.setupUi(self)
        self.create_custom_controls()

        self.readSettings()

        self.tab_actions()

        # self.collect_defaults()

    def create_custom_controls(self):
        self.saveCustomRepoToListPushButton = QtGui.QPushButton(self.customRepoPathsGroupBox)
        self.saveCustomRepoToListPushButton.setText('Save')
        self.saveCustomRepoToListPushButton.setObjectName("saveCustomRepoToListPushButton")
        self.customRepoPathsLayout.addWidget(self.saveCustomRepoToListPushButton, 1, 6, 1, 1)
        self.saveCustomRepoToListPushButton.hide()

    def eventFilter(self, widget, event):

        if event.type() == QtCore.QEvent.KeyPress and isinstance(widget, QtGui.QLineEdit):
            self.save_button.setEnabled(True)
            self.reset_button.setEnabled(True)

        if event.type() == QtCore.QEvent.MouseButtonPress and isinstance(widget, QtGui.QCheckBox):
            self.save_button.setEnabled(True)
            self.reset_button.setEnabled(True)

        if event.type() == QtCore.QEvent.FocusIn and isinstance(widget, QtGui.QTreeWidget):
            self.save_button.setEnabled(True)
            self.reset_button.setEnabled(True)

        return QtGui.QWidget.eventFilter(self, widget, event)

    def tab_actions(self):
        """
        Actions for the configuration tab
        """

        self.buttonBox.button(QtGui.QDialogButtonBox.Close).clicked.connect(lambda: self.close())

        self.reset_button = self.buttonBox.button(QtGui.QDialogButtonBox.Reset)
        self.reset_button.setEnabled(False)
        self.reset_button.clicked.connect(lambda: self.undo_changes())

        self.buttonBox.button(QtGui.QDialogButtonBox.RestoreDefaults).clicked.connect(lambda: self.restore_defaults())

        self.save_button = self.buttonBox.button(QtGui.QDialogButtonBox.Save)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(lambda: self.perform_save())

        self.projectsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.projectsTreeWidget.customContextMenuRequested.connect(self.open_menu)

        self.generateTicketButton.clicked.connect(self.generate_ticket)

        if self.configToolBox.currentIndex() == 2:
            if not env.Env().get_first_run():
                self.add_projects_items(2)

        # checkinOut page events
        self.checkinOutPage.showEvent = self.checkinOutPage_showEvent

        # checkin page events
        self.checkinPage.showEvent = self.checkinPage_showEvent
        self.addCustomRepoToListPushButton.clicked.connect(self.add_custom_repo_dir)
        self.saveCustomRepoToListPushButton.clicked.connect(self.save_custom_repo_dir)
        self.deleteCustomRepoPushButton.clicked.connect(self.delete_custom_repo_dir)
        self.editCustomRepoPushButton.clicked.connect(self.edit_custom_repo_dir)
        self.customRepoTreeWidget.clicked.connect(self.custom_repo_items_visibility)

        self.configToolBox.currentChanged.connect(self.add_projects_items)

    def generate_ticket(self):
        login = self.userNameLineEdit.text()
        password = self.passwordLineEdit.text()
        host = env.Env().get_server()
        project = env.Env().get_project()

        tc.server_auth(host, project, login, password, True)

        env.Env().set_project(project)
        env.Env().set_first_run(False)
        env.Env().set_user(login)

    def create_assets_tree(self):
        self.asstes_tree = tc.query_assets_names()
        for name, value in self.asstes_tree.iteritems():
            self.top_item = QtGui.QTreeWidgetItem()
            self.top_item.setCheckState(0, QtCore.Qt.Unchecked)
            if not name:
                name = 'Untyped'
            self.top_item.setText(0, name.capitalize())
            self.processTreeWidget.addTopLevelItem(self.top_item)
            for item in value:
                self.child_item = QtGui.QTreeWidgetItem()
                if item['title']:
                    item_title = item['title'].capitalize()
                else:
                    item_title = 'Unnamed'
                item_code = item['code']
                self.child_item.setText(0, item_title)
                self.child_item.setText(1, item_code)
                self.child_item.setData(0, QtCore.Qt.UserRole, item)
                self.child_item.setCheckState(0, QtCore.Qt.Unchecked)
                self.top_item.addChild(self.child_item)

    def assets_tree_check_state(self):
        pass

    def checkinOutPage_showEvent(self, *args, **kwargs):
        if self.processTreeWidget.topLevelItemCount() == 0:
            self.create_assets_tree()

    def checkinPage_showEvent(self, *args, **kwargs):
        """
        # TODO get current platform and set proper dirs for linux/wi32
        :param args:
        :param kwargs:
        :return:
        """
        # env.Env().get_default_dirs()
        rep_dirs = env.Env().rep_dirs

        self.assetBaseDirPathLineEdit.setText(rep_dirs['asset_base_dir'][0])
        self.assetBaseDirNameLineEdit.setText(rep_dirs['asset_base_dir'][1])
        self.assetBaseDirCheckBox.setChecked(rep_dirs['asset_base_dir'][2])

        self.sandboxDirPathLineEdit.setText(rep_dirs['win32_sandbox_dir'][0])
        self.sandboxDirNameLineEdit.setText(rep_dirs['win32_sandbox_dir'][1])
        self.sandboxCheckBox.setChecked(rep_dirs['win32_sandbox_dir'][2])

        self.localRepoDirPathLineEdit.setText(rep_dirs['win32_local_repo_dir'][0])
        self.localRepoDirNameLineEdit.setText(rep_dirs['win32_local_repo_dir'][1])
        self.localRepoCheckBox.setChecked(rep_dirs['win32_local_repo_dir'][2])

        self.clientRepoDirPathLineEdit.setText(rep_dirs['win32_client_repo_dir'][0])
        self.clientRepoDirNameLineEdit.setText(rep_dirs['win32_client_repo_dir'][1])
        self.clientRepoCheckBox.setChecked(rep_dirs['win32_client_repo_dir'][2])

        self.handoffDirPathLineEdit.setText(rep_dirs['win32_client_handoff_dir'][0])
        self.handoffCheckBox.setChecked(rep_dirs['win32_client_handoff_dir'][2])

        self.fill_custom_repo_dir(self.custom_repo_item)
        self.customRepoCheckBox.setChecked(rep_dirs['custom_asset_dir']['enabled'])

        self.collect_defaults('checkinPage')

    def add_custom_repo_dir(self):
        print self.custom_repo_item
        if self.custom_repo_item is None:
            d = {
                'path': [],
                'name': [],
                'current': [],
                'visible': [],
            }
            self.custom_repo_item = collections.OrderedDict(d)

        temp_dict = collections.OrderedDict(self.custom_repo_item.copy())

        if (self.customRepoDirNameLineEdit.text() and self.customRepoDirPathLineEdit.text()) != '':
            name = self.customRepoDirNameLineEdit.text()
            path = self.customRepoDirPathLineEdit.text()
            # fill custom repo dict
            temp_dict['path'].append(path)
            temp_dict['name'].append(name)
            temp_dict['current'].append(len(temp_dict['name']) - 1)
            temp_dict['visible'].append(True)

        self.fill_custom_repo_dir(temp_dict)

    def fill_custom_repo_dir(self, in_dict):
        self.customRepoComboBox.clear()
        self.customRepoTreeWidget.clear()

        # adding items to three widget
        for i in in_dict['current']:
            custom_rep_list_item = QtGui.QTreeWidgetItem()
            if in_dict['visible'][i]:
                custom_rep_list_item.setCheckState(0, QtCore.Qt.Checked)
            else:
                custom_rep_list_item.setCheckState(0, QtCore.Qt.Unchecked)
            custom_rep_list_item.setText(0, '')
            custom_rep_list_item.setText(1, in_dict['name'][i])
            custom_rep_list_item.setText(2, in_dict['path'][i])
            self.customRepoTreeWidget.addTopLevelItem(custom_rep_list_item)
            self.customRepoDirNameLineEdit.setText('')
            self.customRepoDirPathLineEdit.setText('')

            self.customRepoComboBox.addItem(in_dict['name'][i])

    def save_custom_repo_dir(self):

        current_idx = self.customRepoComboBox.currentIndex()

        self.saveCustomRepoToListPushButton.hide()
        self.addCustomRepoToListPushButton.show()

        self.custom_repo_item['name'][current_idx] = self.customRepoDirNameLineEdit.text()
        self.custom_repo_item['path'][current_idx] = self.customRepoDirPathLineEdit.text()

        self.fill_custom_repo_dir(self.custom_repo_item)

    def delete_custom_repo_dir(self):
        current_idx = self.customRepoComboBox.currentIndex()

        del self.custom_repo_item['name'][current_idx]
        del self.custom_repo_item['path'][current_idx]
        del self.custom_repo_item['visible'][current_idx]

        self.custom_repo_item['current'] = range(len(self.custom_repo_item['name']))

        self.save_button.setEnabled(True)
        self.reset_button.setEnabled(True)

        self.fill_custom_repo_dir(self.custom_repo_item)

    def edit_custom_repo_dir(self):
        current_idx = self.customRepoComboBox.currentIndex()

        self.addCustomRepoToListPushButton.hide()
        self.saveCustomRepoToListPushButton.show()

        self.customRepoDirNameLineEdit.setText(self.custom_repo_item['name'][current_idx])
        self.customRepoDirPathLineEdit.setText(self.custom_repo_item['path'][current_idx])

    def custom_repo_items_visibility(self, event):
        current_row = event.row()
        current_item = self.customRepoTreeWidget.topLevelItem(current_row)

        if current_item.checkState(0) == QtCore.Qt.CheckState.Checked:
            self.custom_repo_item['visible'][current_row] = True
        else:
            self.custom_repo_item['visible'][current_row] = False

    def restore_defaults(self):
        print('Restore default changes')

    def confirm_saving(self):
        msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'Save preferences?',
                                "<p>Looks like You've made some changes!</p> <p>Perform save?</p>",
                                QtGui.QMessageBox.NoButton, env.Inst().ui_main)

        msb.addButton("Yes", QtGui.QMessageBox.YesRole)
        msb.addButton("No and close", QtGui.QMessageBox.RejectRole)
        msb.addButton("Undo changes", QtGui.QMessageBox.ResetRole)
        msb.addButton("No", QtGui.QMessageBox.NoRole)
        msb.exec_()
        reply = msb.buttonRole(msb.clickedButton())

        if reply == QtGui.QMessageBox.YesRole:
            print 'YES!'

        if reply == QtGui.QMessageBox.ResetRole:
            self.undo_changes()
            print 'UNDO CHANGES!'

        if reply == QtGui.QMessageBox.RejectRole:
            print 'NO CLOSING!'
            self.undo_changes()
            return True

    def campare_changes(self, page):
        if page == 'checkinPage':
            stored_state = self.checkin_page_defaults.copy()

            # self.collect_defaults('checkinPage')

            if stored_state == self.checkin_page_defaults:
                print 'Its equal, can leave'
                return True
            else:
                if self.confirm_saving():
                    return True

            print('Camparing changes')
            # return True

    @staticmethod
    def walk_through_layouts(*args):
        all_widgets = []
        for layout in args:
            for i in range(layout.count()):
                all_widgets.append(layout.itemAt(i).widget())

        return all_widgets

    @staticmethod
    def store_property_by_widget_type(widget, in_dict):

        if isinstance(widget, QtGui.QLineEdit):
            in_dict['QLineEdit']['value'].append(widget.text())
            in_dict['QLineEdit']['obj_name'].append(widget.objectName())

        if isinstance(widget, QtGui.QCheckBox):
            in_dict['QCheckBox']['value'].append(widget.checkState())
            in_dict['QCheckBox']['obj_name'].append(widget.objectName())

        if isinstance(widget, QtGui.QComboBox):
            in_dict['QComboBox']['value'].append(widget.count())
            in_dict['QComboBox']['obj_name'].append(widget.objectName())

        if isinstance(widget, QtGui.QTreeWidget):
            in_dict['QTreeWidget']['value'].append(widget.topLevelItemCount())
            in_dict['QTreeWidget']['obj_name'].append(widget.objectName())

    @staticmethod
    def change_property_by_widget_type(widget, in_dict):

        if isinstance(widget, QtGui.QLineEdit):
            for name, val in zip(in_dict['QLineEdit']['obj_name'], in_dict['QLineEdit']['value']):
                if widget.objectName() == name:
                    widget.setText(val)

        if isinstance(widget, QtGui.QCheckBox):
            for name, val in zip(in_dict['QCheckBox']['obj_name'], in_dict['QCheckBox']['value']):
                if widget.objectName() == name:
                    widget.setCheckState(val)

    def collect_defaults(self, page):

        if page == 'checkinPage':

            d = {
                'QLineEdit': {'obj_name': [], 'value': []},
                'QCheckBox': {'obj_name': [], 'value': []},
                'QComboBox': {'obj_name': [], 'value': []},
                'QTreeWidget': {'obj_name': [], 'value': []},
            }

            self.checkin_page_defaults = collections.OrderedDict(d)

            self.checkin_page_defaults_repo_item = collections.OrderedDict(copy.deepcopy(self.custom_repo_item))

            widgets = self.walk_through_layouts(self.defaultRepoPathsLayout, self.customRepoPathsLayout)

            for widget in widgets:
                if isinstance(widget, (QtGui.QLineEdit, QtGui.QCheckBox, QtGui.QComboBox, QtGui.QTreeWidget)):
                    self.store_property_by_widget_type(widget, self.checkin_page_defaults)
                    widget.installEventFilter(self)

    def undo_changes(self):
        page = 'checkinPage'

        if page == 'checkinPage':

            widgets = self.walk_through_layouts(self.defaultRepoPathsLayout, self.customRepoPathsLayout)

            for widget in widgets:
                if isinstance(widget, (QtGui.QLineEdit, QtGui.QCheckBox, QtGui.QComboBox, QtGui.QTreeWidget)):
                    self.change_property_by_widget_type(widget, self.checkin_page_defaults)

            print self.checkin_page_defaults_repo_item
            print self.custom_repo_item
            self.fill_custom_repo_dir(self.checkin_page_defaults_repo_item)
            self.custom_repo_item = copy.deepcopy(self.checkin_page_defaults_repo_item)

            self.addCustomRepoToListPushButton.show()
            self.saveCustomRepoToListPushButton.hide()

        print('Undoing lats changes!')

    def perform_save(self):
        """
        Scope all Edits for save
        :return:
        """
        # Checkin page save
        if self.campare_changes('checkinPage'):
            rep_dirs = env.Env().rep_dirs
            rep_dirs['custom_asset_dir'] = self.custom_repo_item
            rep_dirs['custom_asset_dir']['enabled'] = self.customRepoCheckBox.checkState()

            rep_dirs['asset_base_dir'][0] = self.assetBaseDirPathLineEdit.text()
            rep_dirs['asset_base_dir'][1] = self.assetBaseDirNameLineEdit.text()
            rep_dirs['asset_base_dir'][2] = self.assetBaseDirCheckBox.checkState()

            rep_dirs['win32_sandbox_dir'][0] = self.sandboxDirPathLineEdit.text()
            rep_dirs['win32_sandbox_dir'][1] = self.sandboxDirNameLineEdit.text()
            rep_dirs['win32_sandbox_dir'][2] = self.sandboxCheckBox.checkState()

            rep_dirs['win32_client_repo_dir'][0] = self.clientRepoDirPathLineEdit.text()
            rep_dirs['win32_client_repo_dir'][1] = self.clientRepoDirNameLineEdit.text()
            rep_dirs['win32_client_repo_dir'][2] = self.clientRepoCheckBox.checkState()

            rep_dirs['win32_local_repo_dir'][0] = self.localRepoDirPathLineEdit.text()
            rep_dirs['win32_local_repo_dir'][1] = self.localRepoDirNameLineEdit.text()
            rep_dirs['win32_local_repo_dir'][2] = self.localRepoCheckBox.checkState()

            rep_dirs['win32_client_handoff_dir'][0] = self.handoffDirPathLineEdit.text()
            rep_dirs['win32_client_handoff_dir'][2] = self.handoffCheckBox.checkState()

            env.Env().set_default_dirs()
            self.collect_defaults('checkinPage')

        if self.current_project != env.Env().get_project():
            env.Env().set_project(self.current_project)
            env.Env().set_namespace(self.current_namespace)
            self.restart()

    def open_menu(self, position):
        indexes = self.projectsTreeWidget.selectedIndexes()

        level = None
        if len(indexes) > 0:

            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1

        if level > 0:
            self.custom_menu = QtGui.QMenu()

            set_current_action = QtGui.QAction('Set as Current', self)
            set_current_action.triggered.connect(self.change_current_project)

            self.custom_menu.addAction(set_current_action)
            self.custom_menu.exec_(self.projectsTreeWidget.viewport().mapToGlobal(position))

    def change_current_project(self):
        # QtGui.QTreeWidgetItem.text()
        # print(self.projectsTreeWidget.currentItem().text(1))

        self.current_project = self.projectsTreeWidget.currentItem().text(1)
        self.current_namespace = self.projectsTreeWidget.currentItem().text(2)
        self.add_projects_items(2)

    def add_projects_items(self, event):

        self.projectsTreeWidget.clear()

        if event == 2 and self.projectsTreeWidget.topLevelItemCount() == 0 and not env.Env().get_first_run():
            projects = tc.query_projects()
        else:
            projects = None

        if projects:
            for key, value in projects.iteritems():
                top_item = QtGui.QTreeWidgetItem()
                if key:
                    title = key.replace('_', ' ').capitalize()
                else:
                    title = 'No Category'
                top_item.setText(0, title)
                self.projectsTreeWidget.addTopLevelItem(top_item)
                self.projectsTreeWidget.header().resizeSection(0, 200)
                top_item.setForeground(0, QtGui.QBrush(QtGui.QColor(128, 128, 128)))
                for project in value:

                    child_item = QtGui.QTreeWidgetItem()

                    if project['is_template']:
                        child_title = project['title'] + ' (template)'
                        child_item.setDisabled(True)
                        child_item.setForeground(0, QtGui.QBrush(QtGui.QColor(50, 150, 175)))
                    else:
                        child_title = project['title']

                    if project['code'] == self.current_project:
                        child_item.setForeground(0, QtGui.QBrush(QtGui.QColor(165, 175, 25)))

                    child_item.setText(0, child_title)
                    child_item.setText(1, project['code'])
                    child_item.setText(2, project['type'])
                    child_item.setText(3, project['status'])

                    top_item.addChild(child_item)
                    top_item.setExpanded(True)

    def restart(self):
        ask_restart = QtGui.QMessageBox.question(self, 'Restart TACTIC Handler?',
                                                 "<p>Looks like You have made changes which require restarting</p>"
                                                 "<p>Perform restart?</p>",
                                                 QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if ask_restart == QtGui.QMessageBox.Yes:
            self.close()
            # if env.Mode().get == 'maya':
            #     reload(ui_maya_dock)
            #     ui_maya_dock.startup(restart=True)
            # else:
            # print(self.parent())
            if not self.first_run:
                self.parent().close()
            self.parent().create_ui_main()
            self.parent().show()

    def checkin_page_setup(self):
        pass

    def readSettings(self):
        """
        Reading Settings
        """
        self.userNameLineEdit.setText(env.Env().get_user())
        self.passwordLineEdit.setText(env.Env().get_user())
        self.tacticEnvLineEdit.setText(env.Env().get_data_dir())
        # self.tacticAssetDirLineEdit.setText(env.Env().rep_dirs['asset_base_dir'][0])
        self.tacticInstallDirLineEdit.setText(env.Env().get_install_dir())
        self.tacticServerLineEdit.setText(env.Env().get_server())
        if env.Mode().get == 'maya':
            self.currentWorkdirLineEdit.setText(cmds.workspace(q=True, dir=True))

        self.settings.beginGroup(env.Mode().get + '/ui_conf')
        self.configToolBox.setCurrentIndex(int(self.settings.value('configToolBox', 0)))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env.Mode().get + '/ui_conf')
        self.settings.setValue('configToolBox', self.configToolBox.currentIndex())
        print('Done ui_conf settings write')
        self.settings.endGroup()

    def closeEvent(self, event):
        if self.campare_changes('checkinPage'):
            self.writeSettings()
            event.accept()
        else:
            event.ignore()
