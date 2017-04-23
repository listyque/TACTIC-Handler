# module Main Ui Classes
# file ui_main_classes.py
# Main Window interface

import collections
from functools import partial
import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
from lib.environment import env_mode, env_inst, env_server
from lib.configuration import cfg_controls
import lib.tactic_classes as tc
import lib.update_functions as uf
import lib.global_functions as gf
import lib.ui.ui_main as ui_main
import lib.ui.ui_main_tabs as ui_main_tabs
import lib.ui.misc.ui_serverside as ui_serverside
import lib.ui.misc.ui_update as ui_update
import lib.ui.misc.ui_create_update as ui_create_update
import ui_checkin_out_tabs_classes
import ui_conf_classes
import ui_my_tactic_classes
import ui_assets_browser_classes
import ui_float_notify_classes
if env_mode.get_mode() == 'maya':
    import lib.maya_functions as mf
    reload(mf)


reload(ui_main)
reload(ui_main_tabs)
reload(ui_serverside)
reload(ui_update)
reload(ui_create_update)
reload(ui_checkin_out_tabs_classes)
reload(ui_conf_classes)
reload(ui_my_tactic_classes)
reload(ui_assets_browser_classes)
reload(ui_float_notify_classes)
reload(tc)
reload(uf)
reload(gf)


class Ui_updateDialog(QtGui.QDialog, ui_update.Ui_updateDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        uf.get_updates_from_server()

        self.updates = uf.get_info_from_updates_folder()

        self.last_version = None
        self.current_version = uf.get_current_version()

        self.load_local_updates()
        self.check_current_version()

        self.controls_actions()

        self.commitPushButton.setHidden(True)

    def load_local_updates(self):

        for update in self.updates:
            update_get = update.get
            item = QtGui.QTreeWidgetItem()
            item.setText(0, uf.get_version(string=True, **update_get('version')).replace('_', '.'))
            item.setText(1, update_get('date'))
            item.setText(2, update_get('changes'))
            item.setText(3, update_get('misc'))
            self.versionsTreeWidget.addTopLevelItem(item)
        if self.updates:
            self.last_version = self.updates[-1].get('version')

        self.versionsTreeWidget.scrollToBottom()

    def check_current_version(self):
        current_version = uf.get_version(string=True, **self.current_version)
        if self.last_version:
            last_version = uf.get_version(string=True, **self.last_version)
        else:
            last_version = current_version

        if current_version == last_version:
            self.updateToLastPushButton.setEnabled(False)
            self.currentVersionlabel.setText('<span style=" color:#00ff00;">{0} (up to date)</span>'.format(
                current_version.replace('_', '.')))
        else:
            self.updateToLastPushButton.setEnabled(True)
            self.currentVersionlabel.setText('<span style=" color:#ff0000;">{0} (new version available)</span>'.format(
                current_version.replace('_', '.')))

    def controls_actions(self):
        self.commitPushButton.clicked.connect(self.create_new_update)
        self.updateToLastPushButton.clicked.connect(self.update_to_last_version)
        self.updateToSelectedPushButton.clicked.connect(self.update_to_selected_version)
        self.currentVersionlabel.mouseDoubleClickEvent = self.currentVersionlabel_double_click

    def currentVersionlabel_double_click(self, event):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ControlModifier:
            self.commitPushButton.setHidden(False)

    def update_to_last_version(self):
        uf.save_current_version(self.last_version)
        self.current_version = uf.get_current_version()
        self.check_current_version()
        archive_path = uf.get_update_archive_from_server(self.updates[-1].get('update_archive'))
        uf.update_from_archive(archive_path)
        env_inst.ui_main.restart_for_update_ui_main()

    def update_to_selected_version(self):
        pass

    def create_new_update(self):
        self.create_new_update_dialog = Ui_createUpdateDialog(self)
        self.create_new_update_dialog.show()


class Ui_createUpdateDialog(QtGui.QDialog, ui_create_update.Ui_createUpdateDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        current_datetime = QtCore.QDateTime.currentDateTime()
        self.dateEdit.setDateTime(current_datetime)
        self.initial_fill_version_spinbox()

        self.controls_actions()

    def initial_fill_version_spinbox(self):
        version_dict = uf.get_current_version()
        self.majorSpinBox.setValue(int(version_dict['major']))
        self.minorSpinBox.setValue(int(version_dict['minor']))
        self.buildSpinBox.setValue(int(version_dict['build']))
        self.revisionSpinBox.setValue(int(version_dict['revision']))

    def controls_actions(self):
        self.createUpdatePushButton.clicked.connect(self.commit_update_to_json)

    def commit_update_to_json(self):
        args = self.majorSpinBox.text(),\
               self.minorSpinBox.text(),\
               self.buildSpinBox.text(),\
               self.revisionSpinBox.text()
        current_ver_dict = uf.get_version(*args)
        current_ver_str = uf.get_version(*args, string=True)
        data_dict = {
            'version': current_ver_dict,
            'date': self.dateEdit.text(),
            'changes': self.changesPlainTextEdit.toPlainText(),
            'misc': self.miscPlainTextEdit.toPlainText(),
            'remove_list': [],
            'update_archive': '{0}.tar.gz'.format(current_ver_str)
        }
        uf.save_json_to_path('{0}/updates/{1}.json'.format(env_mode.get_current_path(), current_ver_str), data_dict)
        uf.save_current_version(current_ver_dict)
        uf.create_update_archive('{0}/updates/{1}.tar.gz'.format(env_mode.get_current_path(), current_ver_str))
        uf.create_updates_list()
        self.close()

    def create_tar_gz_archive(self):
        pass


class Ui_serverScriptEditForm(QtGui.QDialog, ui_serverside.Ui_scriptEditForm):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.controls_actions()

    def controls_actions(self):
        self.runScriptPushButton.clicked.connect(self.run_script)

    def run_script(self):

        code = self.scriptTextEdit.toPlainText()
        code_dict = {
            'code': code
        }

        result = tc.server_start().execute_python_script('', kwargs=code_dict)
        import pprint
        if not result['info']['spt_ret_val']:
            self.stackTraceTextEdit.setText(str(result['status']))
        else:
            self.stackTraceTextEdit.setText(pprint.pformat(result['info']['spt_ret_val']))

        # self.scriptTextEdit.setText('AZZZAZAZA')


class Ui_mainTabs(QtGui.QWidget, ui_main_tabs.Ui_mainTabsForm):
    def __init__(self, project_code, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        env_inst.ui_main_tabs[project_code] = self

        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/main_ui_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)

        self.setupUi(self)
        self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
        self.checkin_out_config = cfg_controls.get_checkin_out()
        self.isCreated = False

        self.project = env_inst.projects.get(project_code)
        self.current_project = self.project.info['code']
        self.current_namespace = self.project.info['type']

        if self.checkin_out_config_projects and self.checkin_out_config:
            if gf.get_value_from_config(self.checkin_out_config, 'controlsTabsFilterGroupBox', 'QGroupBox'):
                self.customize_controls_tabs()

        self.create_ui_main_tabs()

    def customize_controls_tabs(self):
        if self.checkin_out_config_projects:
            project_tabs_list = self.checkin_out_config_projects.get(self.current_project)
            if gf.get_value_from_config(self.checkin_out_config, 'applyToAllProjectsRadioButton', 'QRadioButton'):
                tabs_list = self.checkin_out_config_projects.get('!tabs_list!')
            elif project_tabs_list:
                tabs_list = project_tabs_list['tabs_list']
            else:
                tabs_list = None
            if tabs_list:
                for i, tab in enumerate(tabs_list):
                    if tab[0] == 'Checkin / Checkout':
                        if not tab[2]:
                            self.main_tabWidget.removeTab(self.get_tab_index(self.checkInOutTab))
                        else:
                            self.main_tabWidget.insertTab(i, self.checkInOutTab, tab[1])
                    # if tab[0] == 'Checkin':
                    #     if not tab[2]:
                    #         self.main_tabWidget.removeTab(self.get_tab_index(self.checkInTab))
                    #     else:
                    #         self.main_tabWidget.insertTab(i, self.checkInTab, tab[1])
                    if tab[0] == 'My Tactic':
                        if not tab[2]:
                            self.main_tabWidget.removeTab(self.get_tab_index(self.myTacticTab))
                        else:
                            self.main_tabWidget.insertTab(i, self.myTacticTab, tab[1])
                    if tab[0] == 'Assets Browser':
                        if not tab[2]:
                            self.main_tabWidget.removeTab(self.get_tab_index(self.assetsBrowserTab))
                        else:
                            self.main_tabWidget.insertTab(i, self.assetsBrowserTab, tab[1])

    def create_ui_main_tabs(self):

        self.ui_checkin_checkout = None

        self.stypes_items_thread = tc.ServerThread(self)
        self.threadsActions()
        self.skeyLineEdit_actions()
        self.readSettings()

    def get_tab_index(self, tab_widget):
        return self.main_tabWidget.indexOf(tab_widget)

    def raise_tab(self, tab_widget):
        self.main_tabWidget.setCurrentIndex(self.get_tab_index(tab_widget))

    def threadsActions(self):
        self.stypes_items_thread.finished.connect(lambda:  self.get_stypes(finish_thread=True))

    def get_stypes(self, run_thread=False, finish_thread=False):

        if finish_thread:
            self.stypes_items = tc.treat_result(self.stypes_items_thread)

            if self.stypes_items.isFailed():
                if self.stypes_items.result == QtGui.QMessageBox.ApplyRole:
                    self.stypes_items.run()
                    self.get_stypes(run_thread=True)
                elif self.stypes_items.result == QtGui.QMessageBox.ActionRole:
                    env_inst.offline = True
                    self.parent().self.open_config_dialog()
            else:
                # self.create_ui_checkout()
                # self.create_ui_checkin()
                self.create_checkin_checkout_ui()
                self.toggle_loading_label()
                if env_mode.get_mode() == 'maya':
                    print 'NOW HANDLING HOTKEYS'
                    env_inst.ui_maya_dock.handle_hotkeys()

        if run_thread:
            stypes_cache = None
            # stypes_cache = self.load_object('stypes_items')
            if stypes_cache:
                self.stypes_items = stypes_cache
                if not self.stypes_items_thread.isRunning():
                    self.stypes_items_thread.kwargs = dict(result=self.stypes_items)
                    self.stypes_items_thread.routine = self.empty_return
                    self.stypes_items_thread.start()
            else:
                if not self.stypes_items_thread.isRunning():
                    self.stypes_items_thread.kwargs = dict()
                    self.stypes_items_thread.routine = self.project.get_stypes
                    self.stypes_items_thread.start()

    def create_checkin_checkout_ui(self):
        if not self.stypes_items.isFailed():
            self.ui_checkin_checkout = ui_checkin_out_tabs_classes.Ui_checkInOutTabWidget(
                self.project,
                self.checkInOutTab,
                parent=self
            )
            self.checkInOutLayout.addWidget(self.ui_checkin_checkout)

    # def create_ui_checkout(self):
    #     """
    #     Create Check Out Tab
    #     """
    #     if not self.stypes_items.isFailed():
    #         self.ui_checkout = ui_checkin_out_tabs_classes.Ui_checkOutTabWidget(
    #             self.project,
    #             self.checkOutTab,
    #             parent=self
    #         )
    #         self.checkOutLayout.addWidget(self.ui_checkout)
    #
    # def create_ui_checkin(self, ext=False):
    #     """
    #     Create Check In Tab
    #     """
    #     if not self.stypes_items.isFailed():
    #         self.ui_checkin = ui_checkin_out_tabs_classes.Ui_checkInTabWidget(
    #             self.project,
    #             self.checkInTab,
    #             parent=self
    #         )
    #         self.checkInLayout.addWidget(self.ui_checkin)

    def create_ui_my_tactic(self):
        """
        Create My Tactic Tab
        """
        self.ui_my_tactic = ui_my_tactic_classes.Ui_myTacticWidget(self)
        self.myTacticLayout.addWidget(self.ui_my_tactic)

    def create_ui_float_notify(self):
        """
        Create My Tactic Tab
        """
        self.float_notify = ui_float_notify_classes.Ui_floatNotifyWidget(self)
        self.float_notify.show()
        self.float_notify.setSizeGripEnabled(True)

    def create_ui_assets_browser(self):
        """
        Create Assets Browser Tab
        """
        self.ui_assets_browser = ui_assets_browser_classes.Ui_assetsBrowserWidget(self)
        self.assetsBrowserLayout.addWidget(self.ui_assets_browser)

    def click_on_skeyLineEdit(self, event):
        self.skeyLineEdit.selectAll()

    def skeyLineEdit_actions(self):
        self.skeyLineEdit.mousePressEvent = self.click_on_skeyLineEdit
        self.skeyLineEdit.returnPressed.connect(self.go_by_skey)

    def go_by_skey(self, skey_in=None, relates_to=None):
        # TODO Need to rewrite this according to porjects tabs

        if relates_to:
            self.relates_to = relates_to
        else:
            self.relates_to = None
            if self.main_tabWidget.currentWidget().objectName() == 'checkOutTab':
                self.relates_to = 'checkout'
            if self.main_tabWidget.currentWidget().objectName() == 'checkInTab':
                self.relates_to = 'checkin'

        print(self.relates_to)

        if skey_in:
            skey = tc.parce_skey(skey_in)
        else:
            skey = tc.parce_skey(self.skeyLineEdit.text())

        print(skey)

        common_pipeline_codes = ['snapshot', 'task']
        pipeline_code = None
        if skey:
            if skey.get('pipeline_code') and skey.get('project'):
                if skey.get('project') == env_inst.get_current_project():
                    if skey['pipeline_code'] not in common_pipeline_codes:
                        pipeline_code = u'{namespace}/{pipeline_code}'.format(**skey)
                else:
                    self.wrong_project_message(skey)

        if pipeline_code and self.relates_to in ['checkin', 'checkout']:
            # TODO BUG WITH env_inst.ui_check_tabs!!!
            tab_wdg = env_inst.ui_check_tabs[self.relates_to].sObjTabWidget
            for i in range(tab_wdg.count()):
                if tab_wdg.widget(i).objectName() == pipeline_code:
                    tab_wdg.setCurrentIndex(i)

            tree_wdg = tab_wdg.currentWidget()
            tree_wdg.go_by_skey[0] = True

            if skey.get('context'):
                tree_wdg.go_by_skey[1] = skey

            search_code = skey.get('code')
            tree_wdg.searchLineEdit.setText(search_code)
            tree_wdg.searchOptionsGroupBox.searchCodeRadioButton.setChecked(True)

            tree_wdg.search_results_widget.add_tab(search_code)

            # tree_wdg.add_items_to_results(search_code)

    def wrong_project_message(self, skey):
        print(skey)
        msb = QtGui.QMessageBox(QtGui.QMessageBox.Question,
                                'Item {code}, not belongs to current project!'.format(**skey),
                                '<p>Current project is <b>{0}</b>, switch to <b>{project}</b> related to this item?</p>'.format(
                                    env_server.get_project(), **skey) + '<p>This will restart TACTIC Handler!</p>',
                                QtGui.QMessageBox.NoButton, env_inst.ui_main)
        msb.addButton("Switch to Project", QtGui.QMessageBox.YesRole)
        msb.addButton("Cancel", QtGui.QMessageBox.NoRole)
        msb.exec_()

        reply = msb.buttonRole(msb.clickedButton())

        if reply == QtGui.QMessageBox.YesRole:
            env_server.set_project(skey['project'])
            skey_link = self.skeyLineEdit.text()
            self.close()
            self.create_ui_main()
            self.show()
            self.skeyLineEdit.setText(skey_link)
            self.go_by_skey()

    def create_loading_label(self):
        self.loading_label = QtGui.QLabel()
        self.loading_label.setText('Loading...')
        self.loading_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.loading_label.setVisible(False)

        self.mainTabsLayout.addWidget(self.loading_label, 0, 0)

    def toggle_loading_label(self):
        if self.loading_label.isVisible():
            self.loading_label.setVisible(False)
            self.main_tabWidget.setVisible(True)
            self.skeyLineEdit.setVisible(True)
        else:
            self.loading_label.setVisible(True)
            self.main_tabWidget.setVisible(False)
            self.skeyLineEdit.setVisible(False)

    def readSettings(self):
        """
        Reading Settings
        """

        self.settings.beginGroup('ui_main_tab/{0}/{1}'.format(self.current_namespace, self.current_project))
        self.main_tabWidget.setCurrentIndex(int(self.settings.value('main_tabWidget_currentIndex', 0)))
        # self.main_tabWidget.tabBar().setTabButton(0, QtGui.QTabBar.LeftSide, QtGui.QWidget())
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup('ui_main_tab/{0}/{1}'.format(self.current_namespace, self.current_project))
        self.settings.setValue('main_tabWidget_currentIndex', int(self.main_tabWidget.currentIndex()))
        print('Done ui_main_tab settings write')
        self.settings.endGroup()

    def paintEvent(self, event):
        if not self.isCreated:
            self.create_loading_label()
            self.toggle_loading_label()
            self.get_stypes(run_thread=True)
            # self.
            self.isCreated = True

        env_inst.set_current_project(self.project.info['code'])

    def closeEvent(self, event):

        # if self.ui_checkout:
        #     self.ui_checkout.close()
        if self.ui_checkin_checkout:
            self.ui_checkin_checkout.close()

        self.writeSettings()
        event.accept()


class Ui_Main(QtGui.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/main_ui_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)

        self.projects_docks = collections.OrderedDict()

        if env_mode.is_offline():
            self.create_ui_main_offline()
        else:
            self.create_ui_main()

    def create_project_dock(self, project_code, close_project=True, raise_tab=False):
        if project_code not in self.projects_docks.keys():
            project = env_inst.projects.get(project_code)
            if project:
                dock_widget = QtGui.QDockWidget(self)
                dock_widget.setObjectName(project_code)
                dock_widget.setWindowTitle(project.info['title'].replace('_', ' ').capitalize())
                dock_widget.setMinimumWidth(200)
                dock_widget.setFeatures(
                    QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

                main_tabs_widget = Ui_mainTabs(project_code, dock_widget)
                dock_widget.setWidget(main_tabs_widget)

                self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock_widget)
                for dock in self.projects_docks.values():
                    self.tabifyDockWidget(dock, dock_widget)

                self.projects_docks[project_code] = dock_widget

                dock_widget.show()
                dock_widget.raise_()
            else:
                print('No project with code: {0}'.format(project_code))

        elif close_project:
            self.projects_docks[project_code].widget().close()
            self.projects_docks[project_code].close()
            self.projects_docks[project_code].deleteLater()
            del self.projects_docks[project_code]
            env_inst.cleanup(project_code)

        if raise_tab:
            project_dock = self.projects_docks.get(project_code)
            if project_dock:
                project_dock.show()
                project_dock.raise_()

    def create_ui_main_offline(self):

        env_inst.ui_main = self

        self.setupUi(self)
        self.setWindowTitle('TACTIC handler (OFFLINE)')

        # instance attributes
        self.menu = None
        self.menu_bar_actions()
        self.readSettings()
        self.setIcon()

        self.customize_ui()

    def create_ui_main(self):

        env_inst.ui_main = self

        self.setupUi(self)
        self.setWindowTitle('TACTIC handler')

        # instance attributes
        self.menu = None
        self.mainwidget.deleteLater()

        # Server Threads
        self.projects_items_thread = tc.ServerThread(self)
        # self.update_thread = tc.ServerThread(self)

        self.threadsActions()

        self.query_projects(run_thread=True)

        self.menu_bar_actions()
        self.readSettings()
        self.setIcon()

        self.customize_ui()

        self.check_for_update()

    def check_for_update(self):
        if uf.check_need_update():
            self.label_layout = QtGui.QVBoxLayout(self.menubar)
            self.label_layout.setContentsMargins(0, 0, 6, 0)

            update_label = QtGui.QLabel()
            update_label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
            update_label.setText('<span style=" font-size:8pt; color:#ff0000;">Need update</span>')
            self.label_layout.addWidget(update_label)

    def threadsActions(self):
        self.projects_items_thread.finished.connect(lambda: self.query_projects(finish_thread=True))

    def setIcon(self):
        icon = QtGui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.setWindowIcon(icon)

    def customize_ui(self):
        if env_mode.get_mode() == 'standalone':
            self.actionDock_undock.setVisible(False)

        self.actionExit.setIcon(gf.get_icon('close'))
        self.actionConfiguration.setIcon(gf.get_icon('wrench'))

    def menu_bar_actions(self):
        """
        Actions for the main menu bar
        """

        def close_routine():
            if env_mode.get_mode() == 'maya':
                maya_dock_instances = mf.get_maya_dock_window()
                for maya_dock_instance in maya_dock_instances:
                    maya_dock_instance.close()
                    maya_dock_instance.deleteLater()
                self.close()
            if env_mode.get_mode() == 'standalone':
                self.close()

        self.actionExit.triggered.connect(close_routine)

        self.actionConfiguration.triggered.connect(self.open_config_dialog)

        self.actionApply_to_all_Tabs.triggered.connect(self.apply_current_view)

        self.actionUpdate.triggered.connect(self.update_self)
        self.actionServerside_Script.triggered.connect(self.create_server_side_script_editor)

        self.actionDock_undock.triggered.connect(self.undock_window)

        # deprecated
        # self.main_tabWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        # self.menu = QtGui.QAction("Copy Tab", self.main_tabWidget)
        # self.menu.triggered.connect(self.copy_current_tab)
        # self.main_tabWidget.addAction(self.menu)

    def undock_window(self):
        env_inst.ui_maya_dock.toggle_docking()

    def create_server_side_script_editor(self):

        self.serverside_script_editor = Ui_serverScriptEditForm(self)
        self.serverside_script_editor.show()

    def update_self(self):
        self.update_dialog = Ui_updateDialog(self)

        self.update_dialog.show()

    def open_config_dialog(self):
        conf_dialog = ui_conf_classes.Ui_configuration_dialogWidget(parent=self)
        conf_dialog.show()

    def restart_for_update_ui_main(self):
        if env_mode.get_mode() == 'standalone':
            import main_standalone
            thread = main_standalone.restart()
            thread.finished.connect(self.close)
        if env_mode.get_mode() == 'maya':
            import main_maya
            thread = main_maya.main.restart()
            thread.finished.connect(main_maya.main.close_all_instances)
            # thread.finished.connect(self.close)

    def restart_ui_main(self):
        self.close()
        self.projects_docks = collections.OrderedDict()
        if env_mode.is_online():
            self.create_ui_main()
        else:
            self.create_ui_main_offline()
        self.show()
        return self

    def apply_current_view(self):
        # TODO may be need to be rewriten to use env instance
        current_project_widget = self.projects_docks[env_inst.get_current_project()].widget()

        widget_name = current_project_widget.main_tabWidget.currentWidget().objectName()

        if widget_name == 'checkInOutTab':

            current_project_widget.ui_checkin_checkout.apply_current_view_to_all()

        if widget_name == 'checkOutTab':
            current_project_widget.ui_checkout.apply_current_view_to_all()
        if widget_name == 'checkInTab':
            current_project_widget.ui_checkin.apply_current_view_to_all()

    def fill_projects_to_menu(self):

        all_projects = self.projects_items.result
        all_projects_dicts = []

        for project_name, project in all_projects.iteritems():
            all_projects_dicts.append(project.info)

        projects_by_categories = gf.group_dict_by(all_projects_dicts, 'category')

        for cat_name, projects in projects_by_categories.iteritems():

            if cat_name:
                cat_name = cat_name.replace('_', ' ').capitalize()
            else:
                cat_name = 'No Category'

            category = self.menuProject.addMenu(cat_name)

            for e, project in enumerate(projects):
                # TEMPORARY
                project['is_template'] = False
                # TEMPORARY
                if not project.get('is_template'):
                    project_code = project.get('code')

                    menu_action = QtGui.QAction(self)
                    menu_action.setCheckable(True)

                    if self.opened_projects:
                        if project_code in self.opened_projects:
                            menu_action.setChecked(True)
                    menu_action.setText(project.get('title'))
                    # Don't know why lambda did not work here
                    menu_action.triggered.connect(partial(self.create_project_dock, project_code))
                    category.addAction(menu_action)

    def restore_opened_projects(self):
        self.settings.beginGroup('ui_main')
        self.opened_projects = self.settings.value('opened_projects', '')
        if not isinstance(self.opened_projects, list):
            if self.opened_projects:
                self.opened_projects = [self.opened_projects]

        current_project_code = self.settings.value("current_active_project", '')
        self.settings.endGroup()

        if self.opened_projects:
            for project in self.opened_projects:
                if project:
                    self.create_project_dock(project)

            if current_project_code:
                self.projects_docks[current_project_code].raise_()

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup('ui_main')
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
        self.settings.beginGroup('ui_main')
        if self.windowState() == QtCore.Qt.WindowMaximized:
            state = True
        else:
            state = False
            self.settings.setValue('pos', self.pos())
            self.settings.setValue('size', self.size())
        self.settings.setValue("windowState", int(state))
        self.settings.setValue('opened_projects', self.projects_docks.keys())
        self.settings.setValue('current_active_project', str(env_inst.get_current_project()))

        print('Done main_ui settings write')
        self.settings.endGroup()

    def closeEvent(self, event):
        for dock in self.projects_docks.values():
            dock.widget().close()
            dock.close()
            dock.deleteLater()
            del dock
        self.writeSettings()
        event.accept()

    def query_projects(self, run_thread=False, finish_thread=False):

        if finish_thread:
            self.projects_items = tc.treat_result(self.projects_items_thread)

            if self.projects_items.isFailed():
                if self.projects_items.result == QtGui.QMessageBox.ApplyRole:
                    self.projects_items.run()
                    self.query_projects(run_thread=True)
                elif self.projects_items.result == QtGui.QMessageBox.ActionRole:
                    env_mode.set_offline()
                    self.restart_ui_main()
                    self.open_config_dialog()
                else:
                    env_mode.set_offline()
                    self.restart_ui_main()
            else:
                self.save_object('projects_items', self.projects_items.result)
                env_inst.projects = self.projects_items.result
                self.restore_opened_projects()
                self.fill_projects_to_menu()

        if run_thread:
            projects_cache = self.load_object('projects_items')
            if projects_cache:
                self.projects_items = projects_cache
                if not self.projects_items_thread.isRunning():
                    self.projects_items_thread.kwargs = dict(result=self.projects_items)
                    self.projects_items_thread.routine = self.empty_return
                    self.projects_items_thread.start()
            else:
                if not self.projects_items_thread.isRunning():
                    self.projects_items_thread.kwargs = dict()
                    self.projects_items_thread.routine = tc.get_all_projects
                    self.projects_items_thread.start()

    def save_object(self, name, obj):
        settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/tabs_cache.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)
        settings.beginGroup('tabs_cache/{0}/{1}'.format('namespace', 'project'))
        settings.setValue(name, obj)
        settings.endGroup()

    def load_object(self, name):
        settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/tabs_cache.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)
        settings.beginGroup('tabs_cache/{0}/{1}'.format('namespace', 'project'))
        obj = settings.value(name)
        settings.endGroup()

        return None

    def empty_return(self, result):
        return result

    def closeEventExt(self, event):
        self.ext_window.deleteLater()
        event.accept()
