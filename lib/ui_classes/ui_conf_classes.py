# ui_conf_classes.py
# Configuration window classes

import copy
import collections
import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import lib.environment as env
import lib.tactic_classes as tc
import lib.ui.ui_conf as ui_conf

if env.Mode.get == 'maya':
    # import ui_maya_dock
    import maya.cmds as cmds

reload(ui_conf)


class Ui_configuration_dialogWidget(QtGui.QDialog, ui_conf.Ui_configuration_dialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        env.Inst.ui_conf = self

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')
        self.current_project = env.Env.get_project()
        self.current_namespace = env.Env.get_namespace()

        # Server Threads
        self.query_projects_thread = tc.ServerThread(self)
        self.query_assets_names_thread = tc.ServerThread(self)
        self.server_ping_thread = tc.ServerThread(self)
        self.generate_ticket_thread = tc.ServerThread(self)
        self.threadsActions()

        if env.Inst.offline:
            self.create_ui_conf_offline()
        else:
            env.Env.get_default_dirs()
            self.create_ui_conf()

        self.controls_dict = {
            'QLineEdit': {'obj_name': [], 'value': []},
            'QCheckBox': {'obj_name': [], 'value': []},
            'QComboBox': {'obj_name': [], 'value': []},
            'QTreeWidget': {'obj_name': [], 'value': []},
            'QToolButton': {'obj_name': [], 'value': []},
        }
        # Load saved configs
        self.server_page_init = env.Conf.get_server()
        self.server_page_defaults = None
        self.project_page_init = env.Conf.get_project()
        self.project_page_defaults = None
        self.checkout_page_init = env.Conf.get_checkout()
        self.checkout_page_defaults = None
        if env.Env.rep_dirs:
            self.custom_repo_item_init = env.Env.rep_dirs['custom_asset_dir']
        else:
            self.custom_repo_item_init = None
        self.custom_repo_item_defaults = None
        self.checkin_page_init = env.Conf.get_checkin()
        self.checkin_page_defaults = None
        self.checkinOut_page_init = env.Conf.get_checkin_out()
        self.checkinOut_page_defaults = None
        self.maya_scene_page_init = env.Conf.get_maya_scene()
        self.maya_scene_page_defaults = None

    def create_ui_conf_offline(self):
        self.setupUi(self)

        self.create_custom_controls()
        self.readSettings()
        self.pages_actions()
        self.create_server_page()

        self.configToolBox.setItemEnabled(1, False)
        self.configToolBox.setItemEnabled(2, False)
        self.configToolBox.setItemEnabled(3, False)
        self.configToolBox.setItemEnabled(4, False)
        self.configToolBox.setItemEnabled(5, False)

    def create_ui_conf(self):

        self.setupUi(self)

        self.create_custom_controls()
        self.readSettings()
        self.pages_actions()
        self.create_server_page()

    def switch_to_online_status(self, online=None):
        if online:
            env.Inst.offline = False
            self.create_server_page()
            self.configToolBox.setItemEnabled(1, True)
            self.configToolBox.setItemEnabled(2, True)
            self.configToolBox.setItemEnabled(3, True)
            self.configToolBox.setItemEnabled(4, True)
            self.configToolBox.setItemEnabled(5, True)
        else:
            env.Inst.offline = True
            self.create_server_page()
            self.configToolBox.setItemEnabled(1, False)
            self.configToolBox.setItemEnabled(2, False)
            self.configToolBox.setItemEnabled(3, False)
            self.configToolBox.setItemEnabled(4, False)
            self.configToolBox.setItemEnabled(5, False)

    # collect defaults for individual pages wrap functions
    def collect_server_defaults(self, get_values=False, apply_values=False, store_defaults=False, undo_changes=False):
        self.server_page_defaults, self.server_page_init = self.collect_defaults(
            self.server_page_defaults,
            self.server_page_init,
            [self.authorizationLayout, self.environmentLayout],
            get_values=get_values,
            apply_values=apply_values,
            store_defaults=store_defaults,
            undo_changes=undo_changes,
        )

    def collect_checkout_defaults(self, get_values=False, apply_values=False, store_defaults=False, undo_changes=False):
        self.checkout_page_defaults, self.checkout_page_init = self.collect_defaults(
            self.checkout_page_defaults,
            self.checkout_page_init,
            [self.checkoutMiscOptionsLayout],
            get_values=get_values,
            apply_values=apply_values,
            store_defaults=store_defaults,
            undo_changes=undo_changes,
        )

    def collect_checkin_defaults(self, get_values=False, apply_values=False, store_defaults=False, undo_changes=False):
        self.checkin_page_defaults, self.checkin_page_init = self.collect_defaults(
            self.checkin_page_defaults,
            self.checkin_page_init,
            [self.customRepoPathsLayout, self.defaultRepoPathsLayout, self.checkinMiscOptionsLayout],
            get_values=get_values,
            apply_values=apply_values,
            store_defaults=store_defaults,
            undo_changes=undo_changes,
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

    def create_custom_controls(self):
        self.saveCustomRepoToListPushButton = QtGui.QPushButton(self.customRepoPathsGroupBox)
        self.saveCustomRepoToListPushButton.setText('Save')
        self.saveCustomRepoToListPushButton.setObjectName("saveCustomRepoToListPushButton")
        self.customRepoPathsLayout.addWidget(self.saveCustomRepoToListPushButton, 1, 6, 1, 1)
        self.saveCustomRepoToListPushButton.hide()

    def create_server_page(self):

        if env.Inst.offline:
            self.tacticStatusLable.setText('Status: <b><span style="color:#ff4646;">Unknown</span></b>')
            self.loginStatusLable.setText('Status: <b><span style="color:#ff4646;">Unknown</span></b>')
        else:
            self.tacticStatusLable.setText('Status: <b><span style="color:#a5af19;">Online</span></b>')
            current_ticket = tc.server_start().get_login_ticket()
            if env.Env.get_ticket() == current_ticket:
                self.loginStatusLable.setText('Status: <b><span style="color:#a5af19;">Match</span></b>')
            else:
                self.loginStatusLable.setText('Status: <b><span style="color:#ff4646;">Not Match</span></b>')

    def create_checkin_out_page(self):
        print 'Creating checkinout page'
        self.create_controls_tabs_tree_widget()

    def create_controls_tabs_tree_widget(self):
        if self.controlsTabsTreeWidget.topLevelItemCount() == 0:
            tabs_list = (
                ['Checkout', 'Checkout', True],
                ['Checkin', 'Checkin', True],
                ['My Tactic', 'My Tactic', True],
                ['Assets Browser', 'Assets Browser', True],
            )
            for tab in tabs_list:
                tab_item = QtGui.QTreeWidgetItem((tab[0], tab[1]))
                tab_item.setCheckState(0, QtCore.Qt.Checked)
                tab_item.setFlags(
                    QtCore.Qt.ItemIsSelectable |
                    QtCore.Qt.ItemIsEditable |
                    QtCore.Qt.ItemIsDragEnabled |
                    QtCore.Qt.ItemIsUserCheckable |
                    QtCore.Qt.ItemIsEnabled
                )
                self.controlsTabsTreeWidget.addTopLevelItem(tab_item)

        # controls tabs actions
        self.controlsTabsTreeWidget.itemDoubleClicked.connect(self.edit_tree_item)
        self.controlsTabsMoveUpToolButton.clicked.connect(lambda: self.move_top_level_tree_item(
            self.controlsTabsTreeWidget, 'up'))
        self.controlsTabsMoveDownToolButton.clicked.connect(lambda: self.move_top_level_tree_item(
            self.controlsTabsTreeWidget, 'down'))

    def edit_tree_item(self, item, column):
        if column == 1:
            self.controlsTabsTreeWidget.editItem(item, column)
        else:
            self.controlsTabsTreeWidget.editItem(item, 1)

    def controls_tabs_tree_widget_save(self):
        pass

    @staticmethod
    def move_top_level_tree_item(tree_widget, direction):
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

    def eventFilter(self, widget, event):

        if event.type() == QtCore.QEvent.KeyPress and isinstance(widget, QtGui.QLineEdit):
            self.save_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            current_item = self.configToolBox.currentIndex()
            current_item_text = self.configToolBox.itemText(current_item)
            if current_item_text.find('(changed)') == -1:
                self.configToolBox.setItemText(current_item, '{0}, (changed)'.format(current_item_text))
            if current_item_text.find('(saved)') != -1:
                self.configToolBox.setItemText(current_item, current_item_text.replace(', (saved)', ''))

        if event.type() == QtCore.QEvent.MouseButtonPress and isinstance(widget, QtGui.QCheckBox):
            self.save_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            current_item = self.configToolBox.currentIndex()
            current_item_text = self.configToolBox.itemText(current_item)
            if current_item_text.find('(changed)') == -1:
                self.configToolBox.setItemText(current_item, '{0}, (changed)'.format(current_item_text))
            if current_item_text.find('(saved)') != -1:
                self.configToolBox.setItemText(current_item, current_item_text.replace(', (saved)', ''))

        if event.type() == QtCore.QEvent.FocusIn and isinstance(widget, QtGui.QTreeWidget):
            self.save_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            current_item = self.configToolBox.currentIndex()
            current_item_text = self.configToolBox.itemText(current_item)
            if current_item_text.find('(changed)') == -1:
                self.configToolBox.setItemText(current_item, '{0}, (changed)'.format(current_item_text))
            if current_item_text.find('(saved)') != -1:
                self.configToolBox.setItemText(current_item, current_item_text.replace(', (saved)', ''))

        return QtGui.QWidget.eventFilter(self, widget, event)

    def threadsActions(self):
        self.query_projects_thread.finished.connect(lambda: self.add_projects_items(1))
        self.query_assets_names_thread.finished.connect(self.create_assets_tree)
        self.server_ping_thread.finished.connect(lambda: self.try_connect_to_server(try_connect=True))
        self.generate_ticket_thread.finished.connect(lambda: self.generate_ticket(generate_ticket=True))

    def pages_actions(self):
        """
        Actions for the configuration tab
        """

        # server page actions
        self.connectToServerButton.clicked.connect(lambda: self.try_connect_to_server(run_thread=True))
        self.generateTicketButton.clicked.connect(lambda: self.generate_ticket(run_thread=True))

        self.buttonBox.button(QtGui.QDialogButtonBox.Close).clicked.connect(self.close)

        self.reset_button = self.buttonBox.button(QtGui.QDialogButtonBox.Reset)
        self.reset_button.setEnabled(False)
        self.reset_button.clicked.connect(self.undo_changes)

        self.buttonBox.button(QtGui.QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)

        self.save_button = self.buttonBox.button(QtGui.QDialogButtonBox.Save)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.perform_save)

        self.projectsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.projectsTreeWidget.customContextMenuRequested.connect(self.open_menu)

        # server page events
        self.serverPage.showEvent = self.serverPage_showEvent

        # project page events
        self.projectPage.showEvent = self.projectPage_showEvent

        # checkout page events
        self.checkoutPage.showEvent = self.checkoutPage_showEvent

        # checkin page events
        self.checkinPage.showEvent = self.checkinPage_showEvent
        self.addCustomRepoToListPushButton.clicked.connect(self.add_custom_repo_dir)
        self.saveCustomRepoToListPushButton.clicked.connect(self.save_custom_repo_dir)
        self.deleteCustomRepoPushButton.clicked.connect(self.delete_custom_repo_dir)
        self.editCustomRepoPushButton.clicked.connect(self.edit_custom_repo_dir)
        self.customRepoTreeWidget.clicked.connect(self.custom_repo_items_visibility)

        # checkinOut page events
        self.checkinOutPage.showEvent = self.checkinOutPage_showEvent

        # scenePage page events
        self.currentEnvironmentPage.showEvent = self.currentEnvironmentPage_showEvent

    def generate_ticket(self, run_thread=False, generate_ticket=False):

        if self.passwordLineEdit.text() == self.userNameLineEdit.text():
            generate_ticket = False
            run_thread = False
            msb = QtGui.QMessageBox(
                QtGui.QMessageBox.Information,
                'Generating Ticket',
                'Please enter Password to generate new Ticket',
                QtGui.QMessageBox.NoButton,
                self,
            )
            msb.show()

        if run_thread:
            login = str(self.userNameLineEdit.text())
            password = str(self.passwordLineEdit.text())
            host = str(self.tacticServerLineEdit.text())
            project = env.Env.get_project()

            # print tc.server_auth(host, project, login, password, True)

            if not self.generate_ticket_thread.isRunning():
                self.generate_ticket_thread.kwargs = dict(
                    host=host,
                    project=project,
                    login=login,
                    password=password,
                    get_ticket=True
                )
                self.generate_ticket_thread.routine = tc.server_auth
                self.generate_ticket_thread.start()

        if generate_ticket:
            ticket = tc.treat_result(self.generate_ticket_thread)

            if ticket.isFailed():
                if ticket.result == QtGui.QMessageBox.ApplyRole:
                    ticket.run()
                    self.generate_ticket(generate_ticket=True)
                self.switch_to_online_status(False)

            if not ticket.isFailed():
                self.switch_to_online_status(True)
                self.loginStatusLable.setText('Status: <b><span style="color:#a5af19;">Updated</span></b>')
                env.Env.set_project(env.Env.get_project())
                env.Env.set_server(self.tacticServerLineEdit.text())
                env.Env.set_user(self.userNameLineEdit.text())
                env.Env.get_default_dirs()
                self.custom_repo_item_init = env.Env.rep_dirs['custom_asset_dir']

    def try_connect_to_server(self, run_thread=False, try_connect=False):
        if run_thread:
            env.Env.set_server(str(self.tacticServerLineEdit.text()))
            if not self.server_ping_thread.isRunning():
                self.server_ping_thread.kwargs = dict()
                self.server_ping_thread.routine = tc.server_ping
                self.server_ping_thread.start()

        if try_connect:
            connect = tc.treat_result(self.server_ping_thread)

            if connect.isFailed():
                if connect.result == QtGui.QMessageBox.ApplyRole:
                    connect.run()
                    self.try_connect_to_server(try_connect=True)
                self.switch_to_online_status(False)

            if not connect.isFailed():
                self.switch_to_online_status(True)
                env.Env.get_default_dirs()
                self.custom_repo_item_init = env.Env.rep_dirs['custom_asset_dir']


    def create_assets_tree(self):

        self.processTreeWidget.clear()

        self.assets_names = tc.treat_result(self.query_assets_names_thread)
        for name, value in self.assets_names.result.iteritems():
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

    # Pages show events
    def serverPage_showEvent(self, *args, **kwargs):
        print 'serverPage'
        if not self.server_page_defaults and self.server_page_init:
            self.collect_server_defaults(apply_values=True)
        self.collect_server_defaults()

    def projectPage_showEvent(self, *args, **kwargs):
        print 'add projects_items'
        if not self.query_projects_thread.isRunning():
            self.query_projects_thread.kwargs = dict()
            self.query_projects_thread.routine = tc.query_projects
            self.query_projects_thread.start()

        print 'projectPage'

    def checkoutPage_showEvent(self, *args, **kwargs):
        print 'checkoutPage'
        if not self.checkout_page_defaults and self.checkout_page_init:
            self.collect_checkout_defaults(apply_values=True)
        self.collect_checkout_defaults()

    def checkinPage_showEvent(self, *args, **kwargs):
        """
        # TODO get current platform and set proper dirs for linux/wi32
        :param args:
        :param kwargs:
        :return:
        """
        print 'checkinPage'
        # env.Env.get_default_dirs()
        rep_dirs = env.Env.rep_dirs

        self.assetBaseDirPathLineEdit.setText(rep_dirs['asset_base_dir'][0])
        self.assetBaseDirNameLineEdit.setText(rep_dirs['asset_base_dir'][1])
        self.assetBaseDirCheckBox.setChecked(rep_dirs['asset_base_dir'][2])

        if env.Env.platform == 'Linux':
            print env.Env.platform
        else:
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

        self.fill_custom_repo_dir(self.custom_repo_item_init)
        self.customRepoCheckBox.setChecked(rep_dirs['custom_asset_dir']['enabled'])

        if not self.checkin_page_defaults and self.checkin_page_init:
            self.collect_checkin_defaults(apply_values=True)
        self.collect_checkin_defaults()

    def checkinOutPage_showEvent(self, *args, **kwargs):
        print 'checkinOutPage'
        self.create_checkin_out_page()
        if not self.query_assets_names_thread.isRunning():
            self.query_assets_names_thread.kwargs = dict()
            self.query_assets_names_thread.routine = tc.query_assets_names
            self.query_assets_names_thread.start()
        # if self.processTreeWidget.topLevelItemCount() == 0:
        #     self.create_assets_tree()

    def currentEnvironmentPage_showEvent(self, *args, **kwargs):
        print 'scenePage'

    def add_custom_repo_dir(self):
        print self.custom_repo_item_init
        if self.custom_repo_item_init is None:
            d = {
                'path': [],
                'name': [],
                'current': [],
                'visible': [],
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

    def restore_defaults(self):
        print('Restore default changes')

    def confirm_saving(self, page):

        msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'Save preferences to {0}?'.format(page),
                                "<p>Looks like You've made some changes!</p> <p>Perform save?</p>",
                                QtGui.QMessageBox.NoButton, env.Inst.ui_main)

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

        if page == 'serverPage':
            if self.server_page_defaults:
                self.collect_server_defaults(get_values=True)
                if not self.campare_dicts(self.server_page_init, self.server_page_defaults):
                    return self.confirm_saving('TACTIC Server options')

        if page == 'checkoutPage':
            if self.checkout_page_defaults:
                self.collect_checkout_defaults(get_values=True)
                if not self.campare_dicts(self.checkout_page_init, self.checkout_page_defaults):
                    return self.confirm_saving('Checkout options')

        if page == 'checkinPage':
            if self.checkin_page_defaults:
                self.collect_checkin_defaults(get_values=True)
                if not self.campare_dicts(self.checkin_page_init, self.checkin_page_defaults):
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

    @staticmethod
    def walk_through_layouts(args=None):
        all_widgets = []
        for layout in args:
            for i in range(layout.count()):
                all_widgets.append(layout.itemAt(i).widget())

        return all_widgets

    @staticmethod
    def clear_property_dict(in_dict):
        # clearing all dict
        for i in in_dict.itervalues():
            for val in i.itervalues():
                val[:] = []

    @staticmethod
    def campare_dicts(dict_one, dict_two):
        result = True

        for key, val in dict_one.iteritems():
            for key1, val1 in dict_two.iteritems():
                if key == key1:
                    for i, j in enumerate(val['value']):
                        if j != val1['value'][i]:
                            result = False
                            break

        return result

    @staticmethod
    def store_property_by_widget_type(widget, in_dict):

        if isinstance(widget, QtGui.QLineEdit):
            in_dict['QLineEdit']['value'].append(str(widget.text()))
            in_dict['QLineEdit']['obj_name'].append(widget.objectName())

        if isinstance(widget, QtGui.QCheckBox):
            in_dict['QCheckBox']['value'].append(int(bool(widget.checkState())))
            in_dict['QCheckBox']['obj_name'].append(widget.objectName())

        if isinstance(widget, QtGui.QComboBox):
            in_dict['QComboBox']['value'].append(int(widget.count()))
            in_dict['QComboBox']['obj_name'].append(widget.objectName())

        if isinstance(widget, QtGui.QTreeWidget):
            in_dict['QTreeWidget']['value'].append(int(widget.topLevelItemCount()))
            in_dict['QTreeWidget']['obj_name'].append(widget.objectName())

        if isinstance(widget, QtGui.QToolButton):
            in_dict['QToolButton']['value'].append(str(widget.styleSheet()))
            in_dict['QToolButton']['obj_name'].append(widget.objectName())

    @staticmethod
    def change_property_by_widget_type(widget, in_dict):

        if isinstance(widget, QtGui.QLineEdit):
            for name, val in zip(in_dict['QLineEdit']['obj_name'], in_dict['QLineEdit']['value']):
                if widget.objectName() == name:
                    widget.setText(val)

        if isinstance(widget, QtGui.QCheckBox):
            for name, val in zip(in_dict['QCheckBox']['obj_name'], in_dict['QCheckBox']['value']):
                if widget.objectName() == name:
                    widget.setChecked(val)

    def store_dict_values(self, widgets, out_dict):
        self.clear_property_dict(out_dict)
        for widget in widgets:
            if isinstance(widget, (QtGui.QLineEdit, QtGui.QCheckBox, QtGui.QComboBox, QtGui.QTreeWidget, QtGui.QToolButton)):
                self.store_property_by_widget_type(widget, out_dict)
                widget.installEventFilter(self)

    def apply_dict_values(self, widgets, in_dict):
        for widget in widgets:
            if isinstance(widget, (QtGui.QLineEdit, QtGui.QCheckBox, QtGui.QComboBox, QtGui.QTreeWidget, QtGui.QToolButton)):
                self.change_property_by_widget_type(widget, in_dict)

    def collect_defaults(self, defaults_dict=None, init_dict=None, layouts_list=None, get_values=False, apply_values=False, store_defaults=False, undo_changes=False):
        widgets = self.walk_through_layouts(layouts_list)

        if undo_changes:
            self.apply_dict_values(widgets, defaults_dict)

        if apply_values:
            self.apply_dict_values(widgets, init_dict)

        if get_values:
            self.store_dict_values(widgets, init_dict)

        if store_defaults:
            self.store_dict_values(widgets, defaults_dict)

        if not defaults_dict:
            defaults_dict = copy.deepcopy(self.controls_dict)
            self.store_dict_values(widgets, defaults_dict)

        if not init_dict:
            init_dict = copy.deepcopy(self.controls_dict)

        return defaults_dict, init_dict

    def undo_changes(self, page=None):

        if not page:
            current_page = self.configToolBox.currentWidget().objectName()
        else:
            current_page = page

        if current_page == 'serverPage':
            current_item_text = self.configToolBox.itemText(0)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(0, current_item_text.replace(', (changed)', ''))

            self.collect_server_defaults(undo_changes=True)

        if current_page == 'projectPage':
            current_item_text = self.configToolBox.itemText(1)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(1, current_item_text.replace(', (changed)', ''))

            self.add_projects_items(1)
            # self.collect_server_defaults(undo_changes=True)

        if current_page == 'checkoutPage':
            current_item_text = self.configToolBox.itemText(2)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(2, current_item_text.replace(', (changed)', ''))

            self.collect_checkout_defaults(undo_changes=True)

        if current_page == 'checkinPage':
            current_item_text = self.configToolBox.itemText(3)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(3, current_item_text.replace(', (changed)', ''))

            self.collect_checkin_defaults(undo_changes=True)


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
            self.collect_server_defaults(get_values=True)
            env.Conf.set_server(self.server_page_init)
            self.collect_server_defaults(store_defaults=True)

            current_item_text = self.configToolBox.itemText(0)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(0, current_item_text.replace(', (changed)', ', (saved)'))

        if current_page == 'checkoutPage':
            self.collect_checkout_defaults(get_values=True)
            env.Conf.set_checkout(self.checkout_page_init)
            self.collect_checkout_defaults(store_defaults=True)

            current_item_text = self.configToolBox.itemText(2)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(2, current_item_text.replace(', (changed)', ', (saved)'))

            self.restart()

        if current_page == 'checkinPage':
            self.collect_checkin_defaults(get_values=True)
            env.Conf.set_checkin(self.checkin_page_init)
            self.collect_checkin_defaults(store_defaults=True)

            current_item_text = self.configToolBox.itemText(3)
            if current_item_text.find('(changed)') != -1:
                self.configToolBox.setItemText(3, current_item_text.replace(', (changed)', ', (saved)'))

            # begin filling env dirs
            rep_dirs = env.Env.rep_dirs
            rep_dirs['custom_asset_dir'] = self.custom_repo_item_init
            rep_dirs['custom_asset_dir']['enabled'] = self.customRepoCheckBox.checkState()
            rep_dirs['asset_base_dir'][0] = self.assetBaseDirPathLineEdit.text()
            rep_dirs['asset_base_dir'][1] = self.assetBaseDirNameLineEdit.text()
            rep_dirs['asset_base_dir'][2] = self.assetBaseDirCheckBox.checkState()

            if env.Env.platform == 'Linux':
                rep_dirs['linux_sandbox_dir'][0] = self.sandboxDirPathLineEdit.text()
                rep_dirs['linux_sandbox_dir'][1] = self.sandboxDirNameLineEdit.text()
                rep_dirs['linux_sandbox_dir'][2] = self.sandboxCheckBox.checkState()

                rep_dirs['linux_client_repo_dir'][0] = self.clientRepoDirPathLineEdit.text()
                rep_dirs['linux_client_repo_dir'][1] = self.clientRepoDirNameLineEdit.text()
                rep_dirs['linux_client_repo_dir'][2] = self.clientRepoCheckBox.checkState()

                rep_dirs['linux_local_repo_dir'][0] = self.localRepoDirPathLineEdit.text()
                rep_dirs['linux_local_repo_dir'][1] = self.localRepoDirNameLineEdit.text()
                rep_dirs['linux_local_repo_dir'][2] = self.localRepoCheckBox.checkState()

                rep_dirs['linux_client_handoff_dir'][0] = self.handoffDirPathLineEdit.text()
                rep_dirs['linux_client_handoff_dir'][2] = self.handoffCheckBox.checkState()
            else:
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

            env.Env.set_default_dirs()
            self.restart()

        if self.current_project != env.Env.get_project():
            env.Env.set_project(self.current_project)
            env.Env.set_namespace(self.current_namespace)
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
        self.current_project = self.projectsTreeWidget.currentItem().text(1)
        self.current_namespace = self.projectsTreeWidget.currentItem().text(2)
        self.add_projects_items(1)
        self.save_button.setEnabled(True)
        self.reset_button.setEnabled(True)

        current_item_text = self.configToolBox.itemText(1)
        if current_item_text.find('(changed)') == -1:
            self.configToolBox.setItemText(1, '{0}, (changed)'.format(current_item_text))
        if current_item_text.find('(saved)') != -1:
            self.configToolBox.setItemText(1, current_item_text.replace(', (saved)', ''))

    def add_projects_items(self, event):

        self.projectsTreeWidget.clear()

        if (event == 1) and (self.projectsTreeWidget.topLevelItemCount() == 0):
            projects = tc.treat_result(self.query_projects_thread)

        else:
            projects = None

        if projects:
            for key, value in projects.result.iteritems():
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
            # if env.Mode.get == 'maya':
            #     reload(ui_maya_dock)
            #     ui_maya_dock.startup(restart=True)
            # else:
            # print(self.parent())
            # if env.Inst.offline:
            #     self.parent().close()
            self.parent().create_ui_main()
            self.parent().show()

    def readSettings(self):
        """
        Reading Settings
        """
        self.userNameLineEdit.setText(env.Env.get_user())
        self.passwordLineEdit.setText(env.Env.get_user())
        self.tacticEnvLineEdit.setText(env.Env.get_data_dir())
        self.tacticInstallDirLineEdit.setText(env.Env.get_install_dir())
        self.tacticServerLineEdit.setText(env.Env.get_server())
        if env.Mode.get == 'maya':
            self.currentWorkdirLineEdit.setText(cmds.workspace(q=True, dir=True))

        self.settings.beginGroup(env.Mode.get + '/ui_conf')
        if env.Inst.offline:
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
        self.settings.beginGroup(env.Mode.get + '/ui_conf')
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
        if self.compare_all_changes():
            self.writeSettings()
            env.Inst.ui_conf = None
            event.accept()
        else:
            event.ignore()
