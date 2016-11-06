# module Main Ui Classes
# file ui_main_classes.py
# Main Window interface

import collections
from functools import partial
import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
# import lib.environment as env
from lib.environment import env_mode, env_inst, env_server
from lib.configuration import cfg_controls
# import lib.configuration as cfg
import lib.tactic_classes as tc
import lib.update_functions as uf
import lib.global_functions as gf

if env_mode.get_mode() == 'maya':
    import lib.maya_functions as mf
import lib.ui.ui_main as ui_main
import lib.ui.ui_main_tabs as ui_main_tabs
import lib.ui.misc.ui_serverside as ui_serverside
import ui_checkin_out_tabs_classes
import ui_conf_classes
import ui_my_tactic_classes
import ui_assets_browser_classes
import ui_float_notify_classes

reload(ui_main)
reload(ui_checkin_out_tabs_classes)
reload(ui_conf_classes)
reload(ui_my_tactic_classes)
reload(ui_assets_browser_classes)
reload(ui_serverside)


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
            for i, tab in enumerate(tabs_list):
                if tab[0] == 'Checkout':
                    if not tab[2]:
                        self.main_tabWidget.removeTab(self.main_tabWidget.indexOf(self.checkOutTab))
                    else:
                        self.main_tabWidget.insertTab(i, self.checkOutTab, tab[1])
                if tab[0] == 'Checkin':
                    if not tab[2]:
                        self.main_tabWidget.removeTab(self.main_tabWidget.indexOf(self.checkInTab))
                    else:
                        self.main_tabWidget.insertTab(i, self.checkInTab, tab[1])
                if tab[0] == 'My Tactic':
                    if not tab[2]:
                        self.main_tabWidget.removeTab(self.main_tabWidget.indexOf(self.myTacticTab))
                    else:
                        self.main_tabWidget.insertTab(i, self.myTacticTab, tab[1])
                if tab[0] == 'Assets Browser':
                    if not tab[2]:
                        self.main_tabWidget.removeTab(self.main_tabWidget.indexOf(self.assetsBrowserTab))
                    else:
                        self.main_tabWidget.insertTab(i, self.assetsBrowserTab, tab[1])

    def create_ui_main_tabs(self):

        self.ui_checkout = None
        self.ui_checkin = None

        self.stypes_items_thread = tc.ServerThread(self)
        self.threadsActions()
        self.skeyLineEdit_actions()
        self.readSettings()

    def threadsActions(self):
        self.stypes_items_thread.finished.connect(lambda:  self.get_stypes(finish_thread=True))

    def get_stypes(self, run_thread=False, finish_thread=False):

        if finish_thread:
            self.stypes_items = tc.treat_result(self.stypes_items_thread)

            if self.stypes_items.isFailed():
                if self.stypes_items.result == QtGui.QMessageBox.ApplyRole:
                    self.stypes_items.run()
                    self.query_stypes(run_thread=True)
                elif self.stypes_items.result == QtGui.QMessageBox.ActionRole:
                    env_inst.offline = True
                    self.parent().self.open_config_dialog()
            else:
                self.create_ui_checkout()
                self.create_ui_checkin()
                self.toggle_loading_label()

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

    def create_ui_checkout(self):
        """
        Create Check Out Tab
        """
        if not self.stypes_items.isFailed():
            self.ui_checkout = ui_checkin_out_tabs_classes.Ui_checkOutTabWidget(
                self.project,
                parent=self
            )
            self.checkOutLayout.addWidget(self.ui_checkout)

    def create_ui_checkin(self, ext=False):
        """
        Create Check In Tab
        """
        if not self.stypes_items.isFailed():
            self.ui_checkin = ui_checkin_out_tabs_classes.Ui_checkInTabWidget(
                self.project,
                parent=self
            )
            self.checkInLayout.addWidget(self.ui_checkin)

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
                if skey.get('project') == env_inst.current_project:
                    if skey['pipeline_code'] not in common_pipeline_codes:
                        pipeline_code = u'{namespace}/{pipeline_code}'.format(**skey)
                else:
                    self.wrong_project_message(skey)

        if pipeline_code and self.relates_to in ['checkin', 'checkout']:
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

            tree_wdg.results_group_box.add_tab(search_code)

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
        self.settings.setValue('main_tabWidget_currentIndex', self.main_tabWidget.currentIndex())
        print('Done ui_main_tab settings write')
        self.settings.endGroup()

    def paintEvent(self, event):
        if not self.isCreated:
            self.create_loading_label()
            self.toggle_loading_label()
            self.get_stypes(run_thread=True)
            # self.
            self.isCreated = True

        env_inst.current_project = self.project.info['code']

    def closeEvent(self, event):

        if self.ui_checkout:
            self.ui_checkout.close()
        if self.ui_checkin:
            self.ui_checkin.close()

        self.writeSettings()
        event.accept()


class Ui_Main(QtGui.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        env_inst.ui_main = self

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
            # env_server.get_default_dirs()
            self.create_ui_main()

    def create_project_dock(self, project_code, toggle_state=False):

        if project_code not in self.projects_docks.keys():
            project = env_inst.projects.get(project_code)

            dock_widget = QtGui.QDockWidget(self)
            dock_widget.setObjectName(project_code)
            dock_widget.setWindowTitle(project.info['title'].replace('_', ' ').capitalize())
            dock_widget.setMinimumWidth(200)

            main_tabs_widget = Ui_mainTabs(project_code, dock_widget)
            dock_widget.setWidget(main_tabs_widget)

            self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_widget)
            for dock in self.projects_docks.values():
                self.tabifyDockWidget(dock, dock_widget)

            self.projects_docks[project_code] = dock_widget

            dock_widget.show()
            dock_widget.raise_()

        else:
            self.projects_docks[project_code].widget().close()
            self.projects_docks[project_code].close()
            self.projects_docks[project_code].deleteLater()
            del self.projects_docks[project_code]
            del env_inst.ui_main_tabs[project_code]

    def create_ui_main_offline(self):

        env_inst.ui_main = self
        self.setupUi(self)
        self.setWindowTitle('TACTIC handler (OFFLINE)')

        # instance attributes
        self.menu = None
        self.menu_bar_actions()
        self.readSettings()
        self.setIcon()

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

    def threadsActions(self):
        self.projects_items_thread.finished.connect(lambda: self.query_projects(finish_thread=True))

    def setIcon(self):
        icon = QtGui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.setWindowIcon(icon)

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
            if env_mode.get_mode() == 'standalone':
                self.close()

        self.actionExit.triggered.connect(close_routine)

        self.actionConfiguration.triggered.connect(self.open_config_dialog)

        self.actionApply_to_all_Tabs.triggered.connect(self.apply_current_view)

        self.actionUpdate.triggered.connect(lambda: self.update_self(thread_start=True))
        self.actionServerside_Script.triggered.connect(self.create_server_side_script_editor)

        # deprecated
        # self.main_tabWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        # self.menu = QtGui.QAction("Copy Tab", self.main_tabWidget)
        # self.menu.triggered.connect(self.copy_current_tab)
        # self.main_tabWidget.addAction(self.menu)

    def create_server_side_script_editor(self):

        self.serverside_script_editor = Ui_serverScriptEditForm(self)
        self.serverside_script_editor.show()

    def update_self(self, thread_start=False, update=False):
        uf.check_update()

    def open_config_dialog(self):
        conf_dialog = ui_conf_classes.Ui_configuration_dialogWidget(parent=self)
        conf_dialog.show()

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
        current_project_widget = self.projects_docks[env_inst.current_project].widget()
        widget_name = current_project_widget.main_tabWidget.currentWidget().objectName()

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
                    menu_action.toggled.connect(partial(self.create_project_dock, project_code))
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
        self.settings.setValue('current_active_project', str(env_inst.current_project))

        print('Done main_ui settings write')
        self.settings.endGroup()

    def closeEvent(self, event):
        for dock in self.projects_docks.itervalues():
            dock.widget().close()
            dock.close()
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
                # self.readSettings(True)
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
