# ui_conf_classes.py
# Configuration window classes

import copy
import collections
import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
from lib.environment import env_mode, env_inst, env_server, env_tactic
from lib.configuration import cfg_controls
import lib.tactic_classes as tc
import lib.global_functions as gf
import lib.ui.conf.ui_conf as ui_conf
import lib.ui.conf.ui_serverPage as ui_serverPage
import lib.ui.conf.ui_projectPage as ui_projectPage
import lib.ui.conf.ui_checkoutPage as ui_checkoutPage
import lib.ui.conf.ui_checkinPage as ui_checkinPage
import lib.ui.conf.ui_checkinOutPage as ui_checkinOutPage
import lib.ui.conf.ui_globalPage as ui_globalPage
import lib.ui.conf.ui_mayaPage as ui_mayaPage

if env_mode.get_mode() == 'maya':
    import maya.cmds as cmds

reload(ui_conf)
reload(ui_serverPage)
reload(ui_projectPage)
reload(ui_checkoutPage)
reload(ui_checkinPage)
reload(ui_checkinOutPage)
reload(ui_globalPage)
reload(ui_mayaPage)


class Ui_serverPageWidget(QtGui.QWidget, ui_serverPage.Ui_serverPageWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.page_init = cfg_controls.get_server()
        self.page_defaults = None

        self.ping_thread = tc.ServerThread(self)

        self.create_serverPage()

    def create_serverPage(self):

        self.readSettings()
        self.check_server_status()
        self.threadsActions()
        self.page_actions()

    def threadsActions(self):
        self.ping_thread.finished.connect(lambda: self.try_connect_to_server(try_connect=True))

    def page_actions(self):
        self.connectToServerButton.clicked.connect(lambda: self.try_connect_to_server(run_thread=True))
        self.generateTicketButton.clicked.connect(self.generate_ticket)

    def try_connect_to_server(self, run_thread=False, try_connect=False):

        if run_thread:
            self.save_config()
            if not self.ping_thread.isRunning():
                self.ping_thread.kwargs = dict()
                self.ping_thread.routine = tc.server_fast_ping
                self.ping_thread.start()

            self.ping_thread.wait()

        if try_connect:
            connect = tc.treat_result(self.ping_thread)

            if connect.isFailed():
                if connect.result == QtGui.QMessageBox.ApplyRole:
                    connect.run()
                    self.try_connect_to_server(try_connect=True)
                env_inst.ui_conf.need_restart = True
                if env_inst.ui_conf.need_restart:
                    env_inst.ui_conf.restart(force=True)
                env_inst.ui_conf.switch_to_online_status(False)
                self.check_server_status()

            if not connect.isFailed():
                if connect.result == 'ping_ok':
                    self.tacticStatusLable.setText('Status: <b><span style="color:#a5af19;">Ping OK</span></b>')
                else:
                    if env_inst.ui_conf.need_restart:
                        env_inst.ui_conf.need_restart = False
                        env_inst.ui_conf.restart(force=True)
                    env_inst.ui_conf.switch_to_online_status(True)
                    self.check_server_status()

    def generate_ticket(self):

        self.try_connect_to_server(run_thread=True)
        generate_ticket = False
        if not self.ping_thread.isFailed():
            thread = tc.generate_new_ticket(self.userNameLineEdit.text(), parent=self)
            thread.wait()
            if thread.isFailed():
                tc.treat_result(thread)
            else:
                generate_ticket = True

        if generate_ticket:
            env_inst.ui_conf.switch_to_online_status(True)
            self.check_server_status()
            self.loginStatusLable.setText('Status: <b><span style="color:#a5af19;">Updated</span></b>')
            env_inst.ui_conf.restart(force=True)
            if env_inst.ui_conf.need_restart:
                env_inst.ui_conf.close()

    def collect_defaults(self, get_values=False, apply_values=False, store_defaults=False, undo_changes=False):
        self.page_defaults, self.page_init = gf.collect_defaults(
            self.page_defaults,
            self.page_init,
            [self.serverPageWidgetLayout, self.authorizationLayout, self.environmentLayout, self.proxyGridLayout],
            get_values=get_values,
            apply_values=apply_values,
            store_defaults=store_defaults,
            undo_changes=undo_changes,
            parent=env_inst.ui_conf,
            ignore_list=[QtGui.QLineEdit, QtGui.QTreeWidget, QtGui.QComboBox, QtGui.QRadioButton]
        )

    def check_server_status(self):

        if env_mode.is_offline():
            self.tacticStatusLable.setText('Status: <b><span style="color:#ff4646;">Unknown</span></b>')
            self.loginStatusLable.setText('Status: <b><span style="color:#ff4646;">Unknown</span></b>')
        else:
            self.tacticStatusLable.setText('Status: <b><span style="color:#a5af19;">Ping OK</span></b>')
            current_ticket = tc.server_start().get_login_ticket()
            try:
                tc.server_ping()
            except Exception as expected:
                tc.catch_error_type(expected)
                current_ticket = 'TICKET_ERROR'

            if env_server.get_ticket() == current_ticket:
                self.loginStatusLable.setText('Status: <b><span style="color:#a5af19;">Match</span></b>')
            else:
                self.loginStatusLable.setText('Status: <b><span style="color:#ff4646;">Not Match</span></b>')
                # env_mode.set_offline()
                env_inst.ui_conf.switch_to_online_status(False)
                # env_inst.ui_conf.need_restart = True
                # self.generate_ticket()

    def save_config(self):
        self.collect_defaults(get_values=True)
        cfg_controls.set_server(self.page_init)
        self.collect_defaults(store_defaults=True)

        env_server.set_server(
            server_name=self.tacticServerLineEdit.text(),
        )

        env_server.set_user(
            user_name=self.userNameLineEdit.text(),
        )

        env_server.set_site(
            site_name=self.siteLineEdit.text(),
            enabled=self.usePortalSiteCheckBox.isChecked(),
        )

        env_server.set_proxy(
            proxy_login=self.proxyLoginLineEdit.text(),
            proxy_pass=self.proxyPasswordLineEdit.text(),
            proxy_server=self.proxyServerLineEdit.text(),
            enabled=self.proxyGroupBox.isChecked(),
        )

    def readSettings(self):

        server_presets = env_server.get_server_presets()
        presets_list = server_presets['presets_list']
        current_idx = server_presets['current_idx']

        self.serverPresetsComboBox.addItems(presets_list)
        self.serverPresetsComboBox.setCurrentIndex(current_idx)

        self.userNameLineEdit.setText(env_server.get_user())
        self.tacticServerLineEdit.setText(env_server.get_server())
        # self.tacticEnvLineEdit.setText(env_server.get_data_dir())
        # self.tacticInstallDirLineEdit.setText(env_server.get_install_dir())
        site = env_server.get_site()
        self.siteLineEdit.setText(site['site_name'])
        self.usePortalSiteCheckBox.setChecked(site['enabled'])

        proxy = env_server.get_proxy()
        self.proxyLoginLineEdit.setText(proxy['login'])
        self.proxyPasswordLineEdit.setText(proxy['pass'])
        self.proxyServerLineEdit.setText(proxy['server'])
        self.proxyGroupBox.setChecked(proxy['enabled'])

    def showEvent(self, *args, **kwargs):
        if not self.page_defaults and self.page_init:
            self.collect_defaults(apply_values=True)
        self.collect_defaults()


class Ui_projectPageWidget(QtGui.QWidget, ui_projectPage.Ui_projectPageWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.page_init = cfg_controls.get_project()
        self.page_defaults = None

        self.create_project_page()

    def create_project_page(self):
        self.page_actions()

    def page_actions(self):
        self.projectsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.projectsTreeWidget.customContextMenuRequested.connect(self.open_menu)

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

            set_current_action = QtGui.QAction('Toggle this Project', self)
            set_current_action.triggered.connect(self.activate_current_project)

            self.custom_menu.addAction(set_current_action)
            self.custom_menu.exec_(self.projectsTreeWidget.viewport().mapToGlobal(position))

    def activate_current_project(self):

        project_code = self.projectsTreeWidget.currentItem().text(1)
        env_inst.ui_main.create_project_dock(project_code)

        self.add_projects_items(1)
        env_inst.ui_conf.save_button.setEnabled(True)
        env_inst.ui_conf.reset_button.setEnabled(True)

        current_item_text = env_inst.ui_conf.configToolBox.itemText(1)
        if current_item_text.find('(changed)') == -1:
            env_inst.ui_conf.configToolBox.setItemText(1, '{0}, (changed)'.format(current_item_text))
        if current_item_text.find('(saved)') != -1:
            env_inst.ui_conf.configToolBox.setItemText(1, current_item_text.replace(', (saved)', ''))

    def add_projects_items(self, event):

        self.projectsTreeWidget.clear()

        if (event == 1) and (self.projectsTreeWidget.topLevelItemCount() == 0):
            projects = env_inst.projects
        else:
            projects = None

        if projects:

            all_projects_dicts = []

            for project_name, project in projects.iteritems():
                all_projects_dicts.append(project.info)

            projects_by_categories = gf.group_dict_by(all_projects_dicts, 'category')

            for key, value in projects_by_categories.iteritems():
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

                    if project['code'] in env_inst.ui_main_tabs.keys():
                        child_item.setCheckState(0, QtCore.Qt.Checked)
                        child_item.setForeground(0, QtGui.QBrush(QtGui.QColor(165, 175, 25)))

                    child_item.setText(0, child_title)
                    child_item.setText(1, project['code'])
                    child_item.setText(2, project['type'])
                    child_item.setText(3, project['status'])

                    top_item.addChild(child_item)
                    top_item.setExpanded(True)

    def collect_defaults(self, get_values=False, apply_values=False, store_defaults=False, undo_changes=False):
        self.page_defaults, self.page_init = gf.collect_defaults(
            self.page_defaults,
            self.page_init,
            [self.authorizationLayout, self.environmentLayout],
            get_values=get_values,
            apply_values=apply_values,
            store_defaults=store_defaults,
            undo_changes=undo_changes,
            parent=env_inst.ui_conf,
        )

    def save_config(self):
        env_server.set_project(self.current_project)
        env_server.set_namespace(self.current_namespace)

    def showEvent(self, *args, **kwargs):
        print 'add projects_items'
        # if not self.query_projects_thread.isRunning():
        #     self.query_projects_thread.kwargs = dict()
        #     self.query_projects_thread.routine = tc.query_projects
        #     self.query_projects_thread.start()

        self.add_projects_items(1)

        print 'projectPage'
        # if not self.page_defaults and self.page_init:
        #     self.collect_defaults(apply_values=True)
        # self.collect_defaults()


class Ui_checkoutPageWidget(QtGui.QWidget, ui_checkoutPage.Ui_checkoutPageWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.page_init = cfg_controls.get_checkout()
        self.page_defaults = None

        self.create_checkout_page()

    def create_checkout_page(self):
        pass

    def save_config(self):
        self.collect_defaults(get_values=True)
        cfg_controls.set_checkout(self.page_init)
        self.collect_defaults(store_defaults=True)

    def collect_defaults(self, get_values=False, apply_values=False, store_defaults=False, undo_changes=False):
        self.page_defaults, self.page_init = gf.collect_defaults(
            self.page_defaults,
            self.page_init,
            [self.checkoutMiscOptionsLayout],
            get_values=get_values,
            apply_values=apply_values,
            store_defaults=store_defaults,
            undo_changes=undo_changes,
            parent=env_inst.ui_conf,
            ignore_list=[QtGui.QToolButton, QtGui.QLineEdit, QtGui.QTreeWidget, QtGui.QGroupBox, QtGui.QComboBox, QtGui.QRadioButton]
        )

    def showEvent(self, *args, **kwargs):
        print 'checkoutPage'
        if not self.page_defaults and self.page_init:
            self.collect_defaults(apply_values=True)
        self.collect_defaults()


class Ui_checkinPageWidget(QtGui.QWidget, ui_checkinPage.Ui_checkinPageWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.custom_repo_item_init = env_tactic.get_custom_dir()['value']
        self.custom_repo_item_defaults = None
        self.page_init = cfg_controls.get_checkin()
        self.page_defaults = None

        self.create_checkin_page()
        self.controls_actions()

    def create_checkin_page(self):
        self.saveCustomRepoToListPushButton = QtGui.QPushButton(self.customRepoPathsGroupBox)
        self.saveCustomRepoToListPushButton.setText('Save')
        self.saveCustomRepoToListPushButton.setObjectName("saveCustomRepoToListPushButton")
        self.customRepoPathsLayout.addWidget(self.saveCustomRepoToListPushButton, 1, 6, 1, 1)
        self.saveCustomRepoToListPushButton.hide()

    def controls_actions(self):
        self.addCustomRepoToListPushButton.clicked.connect(self.add_custom_repo_dir)
        self.saveCustomRepoToListPushButton.clicked.connect(self.save_custom_repo_dir)
        self.deleteCustomRepoPushButton.clicked.connect(self.delete_custom_repo_dir)
        self.editCustomRepoPushButton.clicked.connect(self.edit_custom_repo_dir)
        self.customRepoTreeWidget.clicked.connect(self.custom_repo_items_visibility)

    def add_custom_repo_dir(self):
        print self.custom_repo_item_init
        if self.custom_repo_item_init is None:
            d = {
                'path': [],
                'name': [],
                'current': [],
                'visible': [],
                'color': [],
            }
            self.custom_repo_item_init = collections.OrderedDict(d)

        temp_dict = collections.OrderedDict(self.custom_repo_item_init.copy())

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

        self.custom_repo_item_init['name'][current_idx] = self.customRepoDirNameLineEdit.text()
        self.custom_repo_item_init['path'][current_idx] = self.customRepoDirPathLineEdit.text()

        self.fill_custom_repo_dir(self.custom_repo_item_init)

    def delete_custom_repo_dir(self):
        current_idx = self.customRepoComboBox.currentIndex()

        del self.custom_repo_item_init['name'][current_idx]
        del self.custom_repo_item_init['path'][current_idx]
        del self.custom_repo_item_init['visible'][current_idx]

        self.custom_repo_item_init['current'] = range(len(self.custom_repo_item_init['name']))

        self.save_button.setEnabled(True)
        self.reset_button.setEnabled(True)

        self.fill_custom_repo_dir(self.custom_repo_item_init)

    def edit_custom_repo_dir(self):
        current_idx = self.customRepoComboBox.currentIndex()

        self.addCustomRepoToListPushButton.hide()
        self.saveCustomRepoToListPushButton.show()

        self.customRepoDirNameLineEdit.setText(self.custom_repo_item_init['name'][current_idx])
        self.customRepoDirPathLineEdit.setText(self.custom_repo_item_init['path'][current_idx])

    def custom_repo_items_visibility(self, event):
        current_row = event.row()
        current_item = self.customRepoTreeWidget.topLevelItem(current_row)

        if current_item.checkState(0) == QtCore.Qt.CheckState.Checked:
            self.custom_repo_item_init['visible'][current_row] = True
        else:
            self.custom_repo_item_init['visible'][current_row] = False

    def collect_defaults(self, get_values=False, apply_values=False, store_defaults=False, undo_changes=False):
        self.page_defaults, self.page_init = gf.collect_defaults(
            self.page_defaults,
            self.page_init,
            [self.customRepoPathsLayout, self.defaultRepoPathsLayout, self.checkinMiscOptionsLayout],
            get_values=get_values,
            apply_values=apply_values,
            store_defaults=store_defaults,
            undo_changes=undo_changes,
            parent=env_inst.ui_conf,
            ignore_list=[QtGui.QComboBox, QtGui.QRadioButton, QtGui.QGroupBox, QtGui.QTreeWidget]
        )

        if not self.custom_repo_item_defaults:
            self.custom_repo_item_defaults = copy.deepcopy(self.custom_repo_item_init)

        if undo_changes:
            self.fill_custom_repo_dir(self.custom_repo_item_defaults)
            self.custom_repo_item_init = copy.deepcopy(self.custom_repo_item_defaults)

            # print self.custom_repo_item_defaults
            # print self.custom_repo_item_init

            self.addCustomRepoToListPushButton.show()
            self.saveCustomRepoToListPushButton.hide()

    def save_config(self):
        self.collect_defaults(get_values=True)
        cfg_controls.set_checkin(self.page_init)
        self.collect_defaults(store_defaults=True)

        # begin filling env dirs
        values = [
            self.assetBaseDirPathLineEdit.text(),
            self.assetBaseDirNameLineEdit.text(),
            'rgb(128,128,128)',
            'base',
            bool(int(self.assetBaseDirCheckBox.checkState()))
        ]
        env_tactic.set_base_dir('base', values)

        values = [
            self.sandboxDirPathLineEdit.text(),
            self.sandboxDirNameLineEdit.text(),
            'rgb(128,128,128)',
            'sandbox',
            bool(int(self.sandboxCheckBox.checkState()))
        ]
        env_tactic.set_base_dir('sandbox', values)

        values = [
            self.localRepoDirPathLineEdit.text(),
            self.localRepoDirNameLineEdit.text(),
            'rgb(128,128,128)',
            'local',
            bool(int(self.localRepoCheckBox.checkState()))
        ]
        env_tactic.set_base_dir('local', values)

        values = [
            self.clientRepoDirPathLineEdit.text(),
            self.clientRepoDirNameLineEdit.text(),
            'rgb(128,128,128)',
            'client',
            bool(int(self.clientRepoCheckBox.checkState()))
        ]
        env_tactic.set_base_dir('client', values)

        values = [
            self.handoffDirPathLineEdit.text(),
            'Handoff',
            '',
            'handoff_client',
            bool(int(self.handoffCheckBox.checkState()))
        ]
        env_tactic.set_base_dir('handoff_client', values)

        #TODO Custom dirs

        # rep_dirs['custom_asset_dir'] = self.custom_repo_item_init
        # rep_dirs['custom_asset_dir']['enabled'] = int(self.customRepoCheckBox.checkState())

        env_tactic.save_base_dirs()

    def showEvent(self, *args, **kwargs):

        self.fill_custom_repo_dir(self.custom_repo_item_init)
        # self.customRepoCheckBox.setChecked(rep_dirs['custom_asset_dir']['enabled'])

        print 'checkinPage'
        if not self.page_defaults and self.page_init:
            self.collect_defaults(apply_values=True)

        value = env_tactic.get_base_dir('base')['value']
        self.assetBaseDirPathLineEdit.setText(value[0])
        self.assetBaseDirNameLineEdit.setText(value[1])
        self.assetBaseDirCheckBox.setChecked(value[4])

        value = env_tactic.get_base_dir('sandbox')['value']
        self.sandboxDirPathLineEdit.setText(value[0])
        self.sandboxDirNameLineEdit.setText(value[1])
        self.sandboxCheckBox.setChecked(value[4])

        value = env_tactic.get_base_dir('local')['value']
        self.localRepoDirPathLineEdit.setText(value[0])
        self.localRepoDirNameLineEdit.setText(value[1])
        self.localRepoCheckBox.setChecked(value[4])

        value = env_tactic.get_base_dir('client')['value']
        self.clientRepoDirPathLineEdit.setText(value[0])
        self.clientRepoDirNameLineEdit.setText(value[1])
        self.clientRepoCheckBox.setChecked(value[4])

        value = env_tactic.get_base_dir('client_handoff')['value']
        self.handoffDirPathLineEdit.setText(value[0])
        self.handoffCheckBox.setChecked(value[4])

        self.collect_defaults()


class Ui_checkinOutPageWidget(QtGui.QWidget, ui_checkinOutPage.Ui_checkinOutPageWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.opened_projects = env_inst.ui_main_tabs.keys()
        self.selected_project = None

        self.page_init = cfg_controls.get_checkin_out()
        self.page_defaults = None

        self.page_init_projects = cfg_controls.get_checkin_out_projects()
        self.page_defaults_projects = None

        self.create_checkin_out_page()

    def create_checkin_out_page(self):
        self.add_projects_items(1)
        self.controls_actions()

    def controls_actions(self):

        self.projectsDisplayTreeWidget.itemClicked.connect(self.projects_tree_widget_click)
        self.processTreeWidget.itemChanged.connect(self.process_tree_changed)
        self.controlsTabsTreeWidget.itemChanged.connect(self.controls_tree_changed)
        self.applyToAllProjectsRadioButton.toggled.connect(self.switch_controls_per_project)
        self.applyToAllProjectsPushButton.clicked.connect(self.apply_current_controls_to_all)

        # controls tabs actions
        self.controlsTabsTreeWidget.itemDoubleClicked.connect(self.edit_tree_item)
        self.controlsTabsMoveUpToolButton.clicked.connect(lambda: self.move_top_level_tree_item(
            self.controlsTabsTreeWidget, 'up'))
        self.controlsTabsMoveDownToolButton.clicked.connect(lambda: self.move_top_level_tree_item(
            self.controlsTabsTreeWidget, 'down'))

    @staticmethod
    def get_tabs_list():
        return [
            ['Checkout', 'Checkout', True],
            ['Checkin', 'Checkin', True],
            ['My Tactic', 'My Tactic', True],
            ['Assets Browser', 'Assets Browser', True],
        ]

    def apply_current_controls_to_all(self):
        for key, val in self.page_init_projects.iteritems():
            if key != '!tabs_list!':
                self.page_init_projects[key]['tabs_list'] = self.collect_controls_tree_values()

        cfg_controls.set_checkin_out_projects(self.page_init_projects)

    def init_per_projects_config_dict(self):
        projects_dict = {}
        for project in env_inst.projects:
            projects_dict[project] = {}
        for project in env_inst.projects:
            tabs_list = self.get_tabs_list()
            projects_dict[project]['tabs_list'] = tabs_list
            projects_dict[project]['stypes_list'] = None

        projects_dict['!tabs_list!'] = self.get_tabs_list()
        self.page_init_projects = projects_dict

    def switch_controls_per_project(self, state):
        if state:
            self.load_to_controls_tabs_tree_widget(self.page_init_projects['!tabs_list!'])
        elif self.selected_project:
            self.load_to_controls_tabs_tree_widget(self.page_init_projects[self.selected_project]['tabs_list'])

    def projects_tree_widget_click(self, item):
        project_code = item.text(1)
        if project_code:
            # check if we have current project
            if not self.page_init_projects.get(project_code):
                self.init_per_projects_config_dict()

            if self.applyToAllProjectsRadioButton.isChecked():
                self.load_to_controls_tabs_tree_widget(self.page_init_projects['!tabs_list!'])
            else:
                self.load_to_controls_tabs_tree_widget(self.page_init_projects[project_code]['tabs_list'])
            self.load_project_stypes(project_code)

        self.selected_project = project_code

    def load_project_stypes(self, project_code):
        project = env_inst.projects[project_code]
        if not project.stypes:
            project.get_stypes()

        exclude_list = self.page_init_projects[project_code]['stypes_list']

        if not exclude_list:
            self.processTreeWidget.clear()
            if env_inst.projects[project_code].stypes:
                self.create_process_tree_widget(project_code)
                self.page_init_projects[project_code]['stypes_list'] = self.collect_process_tree_values()
        else:
            self.processTreeWidget.clear()
            if env_inst.projects[project_code].stypes:
                self.create_process_tree_widget(project_code, exclude_list)

    def controls_tree_changed(self):
        if self.applyToAllProjectsRadioButton.isChecked():
            self.page_init_projects['!tabs_list!'] = self.collect_controls_tree_values()
        elif self.selected_project:
            self.page_init_projects[self.selected_project]['tabs_list'] = self.collect_controls_tree_values()

        env_inst.ui_conf.set_page_status()

    def collect_controls_tree_values(self):
        tabs_list = []
        for i in range(self.controlsTabsTreeWidget.topLevelItemCount()):
            top_item = self.controlsTabsTreeWidget.topLevelItem(i)
            check_state = True
            if top_item.checkState(0) == QtCore.Qt.CheckState.Unchecked:
                check_state = False
            tabs_list.append([top_item.text(0), top_item.text(1), check_state])

        return tabs_list

    def process_tree_changed(self, item):
        # Mass unchecking by top item
        if item.childCount() > 0:
            for i in range(item.childCount()):
                if item.checkState(0) == QtCore.Qt.CheckState.Unchecked:
                    item.child(i).setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.child(i).setCheckState(0, QtCore.Qt.Checked)

        self.page_init_projects[self.selected_project]['stypes_list'] = self.collect_process_tree_values()
        env_inst.ui_conf.set_page_status()

    def collect_process_tree_values(self):
        exclude_list = []
        for i in range(self.processTreeWidget.topLevelItemCount()):
            top_item = self.processTreeWidget.topLevelItem(i)
            for j in range(top_item.childCount()):
                child_item = top_item.child(j)
                if child_item.checkState(0) == QtCore.Qt.CheckState.Unchecked:
                    exclude_list.append(child_item.text(1))

        return exclude_list

    def create_process_tree_widget(self, project_code, exclude_list=None):
        self.processTreeWidget.clear()

        all_stypes = []

        for stype in env_inst.projects[project_code].stypes.itervalues():
            all_stypes.append(stype.info)

        grouped = gf.group_dict_by(all_stypes, 'type')

        for name, value in grouped.iteritems():
            self.top_item = QtGui.QTreeWidgetItem()
            self.top_item.setCheckState(0, QtCore.Qt.Checked)
            if not name:
                name = 'Untyped'
            self.top_item.setText(0, name.capitalize())
            self.processTreeWidget.addTopLevelItem(self.top_item)
            for item in value:
                self.child_item = QtGui.QTreeWidgetItem()
                if item.get('title'):
                    item_title = item['title'].capitalize()
                else:
                    item_title = 'Unnamed'
                item_code = item['code']
                self.child_item.setText(0, item_title)
                self.child_item.setText(1, item_code)
                self.child_item.setData(0, QtCore.Qt.UserRole, item)
                self.child_item.setCheckState(0, QtCore.Qt.Checked)
                if exclude_list:
                    if item_code in exclude_list:
                        self.child_item.setCheckState(0, QtCore.Qt.Unchecked)
                self.top_item.addChild(self.child_item)

            self.top_item.setExpanded(True)

    def load_to_controls_tabs_tree_widget(self, tabs_list=None):

        self.controlsTabsTreeWidget.clear()

        if not tabs_list:
            tabs_list = self.get_tabs_list()

        for tab in tabs_list:
            tab_item = QtGui.QTreeWidgetItem((tab[0], tab[1]))
            if tab[2]:
                tab_item.setCheckState(0, QtCore.Qt.Checked)
            else:
                tab_item.setCheckState(0, QtCore.Qt.Unchecked)
            tab_item.setFlags(
                QtCore.Qt.ItemIsSelectable |
                QtCore.Qt.ItemIsEditable |
                QtCore.Qt.ItemIsDragEnabled |
                QtCore.Qt.ItemIsUserCheckable |
                QtCore.Qt.ItemIsEnabled
            )
            self.controlsTabsTreeWidget.addTopLevelItem(tab_item)

    def edit_tree_item(self, item, column):
        if column == 1:
            self.controlsTabsTreeWidget.editItem(item, column)
        else:
            self.controlsTabsTreeWidget.editItem(item, 1)

    def controls_tabs_tree_widget_save(self):
        pass

    def move_top_level_tree_item(self, tree_widget, direction):
        current_indexe = tree_widget.selectedIndexes()[0]
        tree_widget.reset()
        taken_item = tree_widget.takeTopLevelItem(current_indexe.row())

        if direction == 'up':
            up_idx = current_indexe.row() - 1
            if up_idx == -1:
                up_idx = tree_widget.topLevelItemCount()
            tree_widget.insertTopLevelItem(up_idx, taken_item)
            tree_widget.setItemSelected(taken_item, True)
        elif direction == 'down':
            down_idx = current_indexe.row() + 1
            if down_idx == tree_widget.topLevelItemCount() + 1:
                down_idx = 0
            tree_widget.insertTopLevelItem(down_idx, taken_item)
            tree_widget.setItemSelected(taken_item, True)

        self.controls_tree_changed()

    def add_projects_items(self, event):

        self.projectsDisplayTreeWidget.clear()

        if (event == 1) and (self.projectsDisplayTreeWidget.topLevelItemCount() == 0):
            projects = env_inst.projects
        else:
            projects = None

        if projects:

            all_projects_dicts = []

            for project_name, project in projects.iteritems():
                all_projects_dicts.append(project.info)

            projects_by_categories = gf.group_dict_by(all_projects_dicts, 'category')

            for key, value in projects_by_categories.iteritems():
                top_item = QtGui.QTreeWidgetItem()
                if key:
                    title = key.replace('_', ' ').capitalize()
                else:
                    title = 'No Category'
                top_item.setText(0, title)
                self.projectsDisplayTreeWidget.addTopLevelItem(top_item)
                self.projectsDisplayTreeWidget.header().resizeSection(0, 150)
                top_item.setForeground(0, QtGui.QBrush(QtGui.QColor(128, 128, 128)))
                for project in value:
                    if not project['is_template']:
                        child_item = QtGui.QTreeWidgetItem()
                        child_title = project['title']

                        if project['code'] in self.opened_projects:
                            # child_item.setCheckState(0, QtCore.Qt.Checked)
                            child_item.setForeground(0, QtGui.QBrush(QtGui.QColor(165, 175, 25)))

                        child_item.setText(0, child_title)
                        child_item.setText(1, project['code'])

                        top_item.addChild(child_item)
                        top_item.setExpanded(True)

    def collect_defaults(self, get_values=False, apply_values=False, store_defaults=False, undo_changes=False):
        self.page_defaults, self.page_init = gf.collect_defaults(
            self.page_defaults,
            self.page_init,
            [self.controlsTabsFilterLayout, self.checkinOutPageWidgetLayout],
            get_values=get_values,
            apply_values=apply_values,
            store_defaults=store_defaults,
            undo_changes=undo_changes,
            parent=env_inst.ui_conf,
            ignore_list=[QtGui.QToolButton, QtGui.QLineEdit, QtGui.QTreeWidget, QtGui.QCheckBox, QtGui.QComboBox]
        )

    def save_config(self):
        self.collect_defaults(get_values=True)
        cfg_controls.set_checkin_out(self.page_init)
        cfg_controls.set_checkin_out_projects(self.page_init_projects)
        self.collect_defaults(store_defaults=True)

    def showEvent(self, *args, **kwargs):
        print 'checkInOutPage'

        if not self.page_defaults and self.page_init:
            self.collect_defaults(apply_values=True)
        self.collect_defaults()

        if not self.page_init_projects:
            self.init_per_projects_config_dict()

        if self.applyToAllProjectsRadioButton.isChecked():
            tabs_list = self.page_init_projects.get('!tabs_list!')
        else:
            if self.page_init_projects.get(env_inst.current_project):
                tabs_list = self.page_init_projects.get(env_inst.current_project)['tabs_list']
            else:
                tabs_list = None

        self.load_to_controls_tabs_tree_widget(tabs_list)


class Ui_globalPageWidget(QtGui.QWidget, ui_globalPage.Ui_globalPageWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)


class Ui_mayaScenePageWidget(QtGui.QWidget, ui_mayaPage.Ui_mayaScenePageWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)


class Ui_configuration_dialogWidget(QtGui.QDialog, ui_conf.Ui_configuration_dialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        env_inst.ui_conf = self

        self.need_restart = None

        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/conf_ui_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)

        self.serverPageWidget = None
        self.projectPageWidget = None
        self.checkoutPageWidget = None
        self.checkinPageWidget = None
        self.checkinOutPageWidget = None
        self.globalConfigPageWidget = None
        self.currentEnvironmentPageWidget = None

        if env_mode.is_offline():
            self.create_ui_conf_offline()
        else:
            self.create_ui_conf()

    def create_ui_conf_offline(self):
        self.need_restart = True
        self.setupUi(self)

        self.readSettings()
        self.controls_actions()
        self.create_server_page()

        for i in range(1, self.configToolBox.count()):
            self.configToolBox.setItemEnabled(i, False)

    def create_ui_conf(self):
        self.need_restart = False
        self.setupUi(self)

        self.readSettings()

        self.controls_actions()

        self.create_server_page()
        self.create_project_page()
        self.create_checkout_page()
        self.create_checkin_page()
        self.create_checkin_out_page()
        self.create_global_config_page()
        self.create_current_environment_page()

    def switch_to_online_status(self, online=None):
        if online:
            env_mode.set_online()
            for i in range(1, self.configToolBox.count()):
                self.configToolBox.setItemEnabled(i, True)
        else:
            env_mode.set_offline()
            for i in range(1, self.configToolBox.count()):
                self.configToolBox.setItemEnabled(i, False)

    def create_server_page(self):
        self.serverPageWidget = Ui_serverPageWidget(self)
        self.serverPageLayout.addWidget(self.serverPageWidget)

    def create_project_page(self):
        self.projectPageWidget = Ui_projectPageWidget(self)
        self.projectPageLayout.addWidget(self.projectPageWidget)

    def create_checkout_page(self):
        self.checkoutPageWidget = Ui_checkoutPageWidget(self)
        self.checkoutPageLayout.addWidget(self.checkoutPageWidget)

    def create_checkin_page(self):
        self.checkinPageWidget = Ui_checkinPageWidget(self)
        self.checkinPageLayout.addWidget(self.checkinPageWidget)

    def create_checkin_out_page(self):
        self.checkinOutPageWidget = Ui_checkinOutPageWidget(self)
        self.checkinOutPageLayout.addWidget(self.checkinOutPageWidget)

    def create_global_config_page(self):
        self.globalConfigPageWidget = Ui_globalPageWidget(self)
        self.globalCofigPageLayout.addWidget(self.globalConfigPageWidget)

    def create_current_environment_page(self):
        if env_mode.get_mode() == 'maya':
            self.currentEnvironmentPageWidget = Ui_mayaScenePageWidget(self)
        else:
            self.currentEnvironmentPageWidget = QtGui.QPushButton('STANDALONE')

        self.currentEnvironmentPageLayout.addWidget(self.currentEnvironmentPageWidget)

    def set_page_status(self):
        self.apply_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        current_item = self.configToolBox.currentIndex()
        current_item_text = self.configToolBox.itemText(current_item)
        if current_item_text.find('(changed)') == -1:
            self.configToolBox.setItemText(current_item, '{0}, (changed)'.format(current_item_text))
        if current_item_text.find('(saved)') != -1:
            self.configToolBox.setItemText(current_item, current_item_text.replace(', (saved)', ', (changed)'))

    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.KeyPress and isinstance(widget, QtGui.QLineEdit):
            self.set_page_status()

        if event.type() == QtCore.QEvent.MouseButtonPress and isinstance(widget, (
                QtGui.QCheckBox,
                QtGui.QGroupBox,
                QtGui.QRadioButton
        )):
            self.set_page_status()

        if event.type() == QtCore.QEvent.FocusIn and isinstance(widget, QtGui.QTreeWidget):
            self.set_page_status()

        return QtGui.QWidget.eventFilter(self, widget, event)

    def controls_actions(self):
        """
        Actions for the configuration tab
        """
        self.buttonBox.button(QtGui.QDialogButtonBox.Close).clicked.connect(self.close)

        self.reset_button = self.buttonBox.button(QtGui.QDialogButtonBox.Reset)
        self.reset_button.setEnabled(False)
        self.reset_button.clicked.connect(self.undo_changes)

        self.buttonBox.button(QtGui.QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)

        self.apply_button = self.buttonBox.button(QtGui.QDialogButtonBox.Apply)
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.perform_save)

    def restore_defaults(self):
        print('Restore default changes')

    def confirm_saving(self, page):

        msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'Save preferences to {0}?'.format(page),
                                "<p>Looks like You've made some changes!</p> <p>Perform save?</p>",
                                QtGui.QMessageBox.NoButton, env_inst.ui_main)

        msb.addButton("Yes", QtGui.QMessageBox.YesRole)
        msb.addButton("Undo changes", QtGui.QMessageBox.ResetRole)
        msb.addButton("Close without save", QtGui.QMessageBox.RejectRole)
        msb.addButton("Cancel", QtGui.QMessageBox.NoRole)
        msb.exec_()
        reply = msb.buttonRole(msb.clickedButton())

        if reply == QtGui.QMessageBox.YesRole:
            return 'perform_save'

        if reply == QtGui.QMessageBox.ResetRole:
            return 'undo_changes'

        if reply == QtGui.QMessageBox.RejectRole:
            return 'exit'

        if reply == QtGui.QMessageBox.NoRole:
            return 'cancel'

    def compare_changes(self, page=None):

        if env_mode.is_online():

            if page == 'serverPage' and self.serverPageWidget:
                if self.serverPageWidget.page_defaults:
                    self.serverPageWidget.collect_defaults(get_values=True)
                    if not gf.campare_dicts(self.serverPageWidget.page_init, self.serverPageWidget.page_defaults):
                        return self.confirm_saving('TACTIC Server options')

            if page == 'checkoutPage' and self.checkoutPageWidget:
                if self.checkoutPageWidget.page_defaults:
                    self.checkoutPageWidget.collect_defaults(get_values=True)
                    if not gf.campare_dicts(self.checkoutPageWidget.page_init, self.checkoutPageWidget.page_defaults):
                        return self.confirm_saving('Checkout options')

            if page == 'checkinPage' and self.checkinPageWidget:
                if self.checkinPageWidget.page_defaults:
                    self.checkinPageWidget.collect_defaults(get_values=True)
                    if not gf.campare_dicts(self.checkinPageWidget.page_init, self.checkinPageWidget.page_defaults):
                        return self.confirm_saving('Checkin options')

    def compare_all_changes(self):
        # walk through all pages, to see any changes made
        for i in range(self.configToolBox.count()):
            current_page = self.configToolBox.widget(i).objectName()
            compare = self.compare_changes(current_page)
            if compare == 'exit':
                return True
            elif compare == 'perform_save':
                self.perform_save(current_page)
            elif compare == 'undo_changes':
                self.undo_changes()
                return False
            elif compare == 'cancel':
                return False

        return True

    def undo_changes(self, page=None):

        if not page:
            current_page = self.configToolBox.currentWidget().objectName()
        else:
            current_page = page

        if current_page == 'serverPage':
            current_item_text = self.configToolBox.itemText(0)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(0, current_item_text.replace(', (changed)', ''))

            self.serverPageWidget.collect_defaults(undo_changes=True)

        if current_page == 'projectPage':
            current_item_text = self.configToolBox.itemText(1)
            print current_item_text
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(1, current_item_text.replace(', (changed)', ''))

            self.projectPageWidget.change_current_project(undo=True)

        if current_page == 'checkoutPage':
            current_item_text = self.configToolBox.itemText(2)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(2, current_item_text.replace(', (changed)', ''))

            self.checkoutPageWidget.collect_defaults(undo_changes=True)

        if current_page == 'checkinPage':
            current_item_text = self.configToolBox.itemText(3)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(3, current_item_text.replace(', (changed)', ''))

            self.checkoutPageWidget.collect_defaults(undo_changes=True)


        # if page == 'checkinPage':
        #
        #     widgets = self.walk_through_layouts(self.defaultRepoPathsLayout, self.customRepoPathsLayout)
        #
        #     for widget in widgets:
        #         if isinstance(widget, (QtGui.QLineEdit, QtGui.QCheckBox, QtGui.QComboBox, QtGui.QTreeWidget)):
        #             self.change_property_by_widget_type(widget, self.checkin_page_init)
        #
        #     print self.checkin_page_defaults_repo_item
        #     print self.custom_repo_item
        #     self.fill_custom_repo_dir(self.checkin_page_defaults_repo_item)
        #     self.custom_repo_item = copy.deepcopy(self.checkin_page_defaults_repo_item)
        #
        #     self.addCustomRepoToListPushButton.show()
        #     self.saveCustomRepoToListPushButton.hide()

        # print('Undoing lats changes!')
        # self.save_button.setEnabled(False)
        # self.reset_button.setEnabled(False)

    def perform_save(self, page=None):
        """
        Scope all Edits for save
        :return:
        """
        if not page:
            current_page = self.configToolBox.currentWidget().objectName()
        else:
            current_page = page

        if current_page == 'serverPage':
            # self.serverPageWidget.save_config()
            self.serverPageWidget.try_connect_to_server(run_thread=True)
            current_item_text = self.configToolBox.itemText(0)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(0, current_item_text.replace(', (changed)', ', (saved)'))

            if env_mode.is_online():
                self.restart(force=True)

        if current_page == 'projectPage':
            self.projectPageWidget.save_config()

            self.restart(force=True)

        if current_page == 'checkoutPage':
            self.checkoutPageWidget.save_config()

            current_item_text = self.configToolBox.itemText(2)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(2, current_item_text.replace(', (changed)', ', (saved)'))

            self.restart(force=True)

        if current_page == 'checkinPage':
            self.checkinPageWidget.save_config()

            current_item_text = self.configToolBox.itemText(3)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(3, current_item_text.replace(', (changed)', ', (saved)'))

            self.restart(force=True)

        if current_page == 'checkinOutPage':
            self.checkinOutPageWidget.save_config()

            current_item_text = self.configToolBox.itemText(4)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(4, current_item_text.replace(', (changed)', ', (saved)'))

            self.restart(force=True)

    def restart(self, force=False):
        if force:
            main_window = env_inst.ui_main
            new_main_window = main_window.restart_ui_main()
            self.setParent(new_main_window)
        else:
            ask_restart = QtGui.QMessageBox.question(self, 'Restart TACTIC Handler?',
                                                     "<p>Looks like You have made changes which require restarting</p>"
                                                     "<p>Perform restart?</p>",
                                                     QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if ask_restart == QtGui.QMessageBox.Yes:
                # self.close()
                main_window = env_inst.ui_main
                new_main_window = main_window.restart_ui_main()
                self.setParent(new_main_window)

    def readSettings(self):
        """
        Reading Settings
        """
        # if env_mode.get_mode() == 'maya':
        #     self.currentWorkdirLineEdit.setText(cmds.workspace(q=True, dir=True))

        self.settings.beginGroup('ui_conf')
        if env_mode.is_offline():
            self.configToolBox.setCurrentIndex(0)
        else:
            self.configToolBox.setCurrentIndex(int(self.settings.value('configToolBox', 0)))
        self.move(self.settings.value('pos', self.pos()))
        self.resize(self.settings.value('size', self.size()))
        if self.settings.value("windowState"):
            if bool(int(self.settings.value("windowState"))):
                self.setWindowState(QtCore.Qt.WindowMaximized)
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup('ui_conf')
        self.settings.setValue('configToolBox', self.configToolBox.currentIndex())
        if self.windowState() == QtCore.Qt.WindowMaximized:
            state = True
        else:
            state = False
            self.settings.setValue('pos', self.pos())
            self.settings.setValue('size', self.size())
        self.settings.setValue("windowState", int(state))
        print('Done ui_conf settings write')
        self.settings.endGroup()

    def closeEvent(self, event):

        # FIXME Double restarting bug

        if self.compare_all_changes():
            self.writeSettings()
            env_inst.ui_conf = None
            event.accept()
        else:
            event.ignore()
