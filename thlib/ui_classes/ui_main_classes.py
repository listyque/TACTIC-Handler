# module Main Ui Classes
# file ui_main_classes.py
# Main Window interface

import collections
from functools import partial
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

from thlib.environment import env_mode, env_inst, dl, env_write_config, env_read_config, cfg_controls, env_api, env_server
import thlib.tactic_classes as tc
import thlib.update_functions as uf
import thlib.global_functions as gf
import thlib.ui.ui_main as ui_main
from thlib.ui_classes.ui_script_editor_classes import Ui_ScriptEditForm
from thlib.ui_classes.ui_update_classes import Ui_updateDialog
import thlib.ui.misc.ui_create_update as ui_create_update
from thlib.ui_classes.ui_custom_qwidgets import Ui_debugLogWidget, Ui_messagesWidget
import ui_checkin_out_tabs_classes
import ui_conf_classes

if env_mode.get_mode() == 'maya':
    import thlib.maya_functions as mf
    reload(mf)


reload(ui_main)
reload(ui_create_update)
reload(ui_checkin_out_tabs_classes)
reload(ui_conf_classes)
#reload(ui_assets_browser_classes)
#reload(ui_float_notify_classes)
reload(tc)
reload(uf)
reload(gf)


class Ui_mainTabs(QtGui.QWidget):
    def __init__(self, project_code, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        env_inst.ui_main_tabs[project_code] = self

        self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
        self.checkin_out_config = cfg_controls.get_checkin_out()
        self.isCreated = False

        self.project = env_inst.projects.get(project_code)
        self.current_project = self.project.info['code']
        self.current_namespace = self.project.info['type']

        self.create_ui()

    def create_ui(self):

        self.ui_checkin_checkout = None
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.create_loading_label()

    def get_tab_index(self, tab_widget):
        return self.main_tabWidget.indexOf(tab_widget)

    def raise_tab(self, tab_widget):
        self.main_tabWidget.setCurrentIndex(self.get_tab_index(tab_widget))

    def get_stypes(self, result=None, run_thread=False):

        if result:
            if self.project.stypes:
                self.create_checkin_checkout_ui()
                self.toggle_loading_label()
                self.ui_checkin_checkout.setHidden(False)
            env_inst.ui_main.set_info_status_text('')

        if run_thread:

            env_inst.ui_main.set_info_status_text(
                '<span style=" font-size:8pt; color:#00ff00;">Getting Search Types</span>')

            def get_stypes_agent():
                return self.project.get_stypes()

            env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

            stypes_items_worker = gf.get_thread_worker(
                get_stypes_agent,
                env_inst.get_thread_pool('server_query/server_thread_pool'),
                result_func=self.get_stypes,
                error_func=gf.error_handle
            )
            stypes_items_worker.start()

    def create_checkin_checkout_ui(self):
        self.ui_checkin_checkout = ui_checkin_out_tabs_classes.Ui_checkInOutTabWidget(
            self.project,
            self,
        )
        self.ui_checkin_checkout.setHidden(True)
        self.main_layout.addWidget(self.ui_checkin_checkout)

    def create_loading_label(self):
        self.loading_label = QtGui.QLabel()
        self.loading_label.setText('Loading...')
        self.loading_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.loading_label.setVisible(False)

        self.main_layout.addWidget(self.loading_label, 0, 0, 0, 0)

    def toggle_loading_label(self):
        if self.loading_label.isVisible():
            self.loading_label.setVisible(False)
        else:
            self.loading_label.setVisible(True)

    def showEvent(self, *args, **kwargs):

        if not self.isCreated:
            self.isCreated = True
            self.toggle_loading_label()
            self.get_stypes(run_thread=True)

        env_inst.set_current_project(self.project.info['code'])

    def closeEvent(self, event):

        if self.ui_checkin_checkout:
            self.ui_checkin_checkout.close()

        event.accept()


class Ui_Main(QtGui.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        self.ui_settings_dict = {}
        self.created = False

        self.create_debuglog_widget()

        if env_mode.is_offline():
            self.create_ui_main_offline()
        else:
            self.create_ui_main()

    def create_project_dock(self, project_code, close_project=True, raise_tab=False):
        if project_code not in self.projects_docks.keys():
            project = env_inst.projects.get(project_code)
            if project:
                if not project.is_template():
                    dock_widget = QtGui.QDockWidget(self)
                    dock_widget.setObjectName(project_code)
                    dock_widget.setWindowTitle(project.info.get('title'))
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
        self.projects_docks = collections.OrderedDict()

        env_inst.ui_main = self

        self.setupUi(self)
        self.setWindowTitle('TACTIC handler (OFFLINE)')

        # instance attributes
        self.menu = None
        self.menu_bar_actions()
        self.menuProject.setEnabled(False)
        self.readSettings()
        self.setIcon()

        self.customize_ui()

    def create_ui_main(self):
        self.projects_docks = collections.OrderedDict()

        env_inst.ui_main = self

        self.setupUi(self)
        self.setWindowTitle('TACTIC Handler')
        self.customize_ui()

        # instance attributes
        self.menu = None
        self.mainwidget.deleteLater()
        self.query_projects()
        self.menu_bar_actions()
        self.menuProject.setEnabled(True)
        self.readSettings()
        self.setIcon()
        self.create_script_editor_widget()
        # self.create_messages_widget()

        self.created = True

    @staticmethod
    def execute_after_all_ui_started():
        # This func is executed after all ui started. File execute_after_start can contain any useful code that
        # should be executed after ui loaded

        from execute_after_start import execute

        execute()

        env_api.start_api_server_app()

    def create_debuglog_widget(self):
        env_inst.ui_debuglog = Ui_debugLogWidget(self)
        env_inst.ui_debuglog.setWindowState(QtCore.Qt.WindowMinimized)

        env_inst.ui_debuglog.show()
        env_inst.ui_debuglog.hide()
        env_inst.ui_debuglog.setWindowState(QtCore.Qt.WindowNoState)

    def create_script_editor_widget(self):
        env_inst.ui_script_editor = Ui_ScriptEditForm(self)

    def create_messages_widget(self):
        env_inst.ui_messages = Ui_messagesWidget(self)

    def create_info_label(self):
        self.label_layout = QtGui.QVBoxLayout(self.menubar)
        self.label_layout.setContentsMargins(0, 0, 6, 0)

        self.info_label = QtGui.QLabel()
        self.info_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.info_label.setText('')
        self.label_layout.addWidget(self.info_label)

    def set_status_text(self, text=''):
        self.setStatusTip(text)

    def set_info_status_text(self, status_text=''):
        self.info_label.setText(status_text)

    def check_for_update(self):
        if uf.check_need_update():
            self.info_label.setText('<span style=" font-size:8pt; color:#ff0000;">Need update</span>')

    def setIcon(self):
        icon = Qt4Gui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.setWindowIcon(icon)

    def customize_ui(self):
        if env_mode.get_mode() == 'standalone':
            self.actionDock_undock.setVisible(False)

        self.actionExit.setIcon(gf.get_icon('window-close', icons_set='mdi'))
        self.actionConfiguration.setIcon(gf.get_icon('settings', icons_set='mdi'))
        self.actionSave_Preferences.setIcon(gf.get_icon('content-save', icons_set='mdi'))
        self.actionReloadCache.setIcon(gf.get_icon('reload', icons_set='mdi'))
        self.actionApply_to_all_Tabs.setIcon(gf.get_icon('hexagon-multiple', icons_set='mdi'))
        self.actionScriptEditor.setIcon(gf.get_icon('script', icons_set='mdi'))
        self.actionDebug_Log.setIcon(gf.get_icon('bug', icons_set='mdi'))
        self.actionUpdate.setIcon(gf.get_icon('update', icons_set='mdi'))
        self.create_info_label()

    def menu_bar_actions(self):
        """
        Actions for the main menu bar
        """

        def close_routine():
            if env_mode.get_mode() == 'maya':

                self.close()

                from thlib.ui_classes.ui_maya_dock import close_all_instances
                close_all_instances()

                # Removing path from sys, so we can run other instance from different path
                import sys
                sys.path.remove(env_mode.get_current_path())

            if env_mode.get_mode() == 'standalone':

                self.close()

        self.actionExit.triggered.connect(close_routine)

        self.actionConfiguration.triggered.connect(self.open_config_dialog)

        self.actionApply_to_all_Tabs.triggered.connect(self.apply_current_view)
        self.actionReloadCache.triggered.connect(self.reload_cache)

        self.actionUpdate.triggered.connect(self.update_self)
        self.actionScriptEditor.triggered.connect(self.open_script_editor)
        self.actionDebug_Log.triggered.connect(lambda: env_inst.ui_debuglog.show())

        # User Menu items
        self.actionMessages.triggered.connect(lambda: env_inst.ui_messages.show())
        self.actionEdit_My_Account.triggered.connect(self.edit_my_account)

        self.actionDock_undock.triggered.connect(self.undock_window)

    def undock_window(self):
        env_inst.ui_maya_dock.toggle_docking()

    def edit_my_account(self):

        print 'Edit my Account'
        from thlib.ui_classes.ui_addsobject_classes import Ui_addTacticSobjectWidget

        login_stype = env_inst.get_stype_by_code('sthpw/login')
        # parent_stype = self.parent_sobject.get_stype()
        # search_key = self.parent_sobject.get_search_key()

        # print search_key

        add_sobject = Ui_addTacticSobjectWidget(
            stype=login_stype,
            parent_stype=None,
            # search_key=search_key,
            parent_search_key=None,
            # view='edit',
            parent=self,
        )

        add_sobject.show()

    # def create_ui_float_notify(self):
    #     self.float_notify = ui_float_notify_classes.Ui_floatNotifyWidget(self)
    #     self.float_notify.show()
    #     self.float_notify.setSizeGripEnabled(True)

    def open_script_editor(self):
        env_inst.ui_script_editor.show()

    def update_self(self):
        if env_mode.is_online():
            self.update_dialog = Ui_updateDialog(self)

            self.update_dialog.show()

    def reload_cache(self):
        tc.get_all_projects_and_logins(True)
        for project in env_inst.projects.values():
            project.query_search_types(True)

        if env_mode.get_mode() == 'maya':
            self.restart_ui_main()
        else:
            self.close()
            gf.restart_app()

    def open_config_dialog(self):
        conf_dialog = ui_conf_classes.Ui_configuration_dialogWidget(parent=self)
        conf_dialog.show()

    def restart_for_update_ui_main(self):

        if env_mode.get_mode() == 'maya':
            # import main_maya
            # thread = main_maya.main.restart()
            from thlib.ui_classes.ui_maya_dock import close_all_instances
            close_all_instances()
            # self.restart_ui_main()
        else:
            self.close()
            gf.restart_app()

        # if env_mode.get_mode() == 'standalone':
        #     import main_standalone
        #     thread = main_standalone.restart()
        #     thread.finished.connect(self.close)
        # if env_mode.get_mode() == 'maya':
        #     import main_maya
        #     thread = main_maya.main.restart()
        #     thread.finished.connect(main_maya.main.close_all_instances)

    def restart_ui_main(self, server_preset=None):
        if server_preset:
            new_server_preset = env_server.get_cur_srv_preset()
            env_server.set_cur_srv_preset(server_preset)

        # Closing main app itself
        self.close()

        # Closing server api
        env_api.close_server()

        if server_preset:
            env_server.set_cur_srv_preset(new_server_preset)

        if env_mode.is_online():
            self.create_ui_main()
        else:
            self.create_ui_main_offline()

        self.show()
        return self

    def apply_current_view(self):
        # TODO may be need to be rewriten to use env instance
        if env_inst.get_current_project():
            current_project_widget = self.projects_docks[env_inst.get_current_project()].widget()

            current_project_widget.ui_checkin_checkout.apply_current_view_to_all()

            # widget_name = current_project_widget.main_tabWidget.currentWidget().objectName()

            # if widget_name == 'checkInOutTab':
            #     current_project_widget.ui_checkin_checkout.apply_current_view_to_all()
            #
            # if widget_name == 'checkOutTab':
            #     current_project_widget.ui_checkout.apply_current_view_to_all()
            #
            # if widget_name == 'checkInTab':
            #     current_project_widget.ui_checkin.apply_current_view_to_all()

    def fill_projects_to_menu(self):

        all_projects_dicts = []

        for project_name, project in env_inst.projects.items():
            if project.get_code() != 'sthpw':
                all_projects_dicts.append(project.info)

        projects_by_categories = gf.group_dict_by(all_projects_dicts, 'category')

        for cat_name, projects in projects_by_categories.items():
            if cat_name:
                cat_name = gf.prettify_text(cat_name, True)
            else:
                cat_name = 'No Category'
            if cat_name != 'Template':
                category = self.menuProject.addMenu(cat_name)

            for e, project in enumerate(projects):
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
        if self.ui_settings_dict:
            self.opened_projects = self.ui_settings_dict.get('opened_projects')
        else:
            self.opened_projects = None
        if not isinstance(self.opened_projects, list):
            if self.opened_projects:
                self.opened_projects = [self.opened_projects]

        if self.opened_projects:
            for project in self.opened_projects:
                if project:
                    self.create_project_dock(project)

            current_project_code = self.ui_settings_dict.get('current_active_project')

            if current_project_code:
                if self.projects_docks.get(current_project_code):
                    self.projects_docks[current_project_code].show()
                    self.projects_docks[current_project_code].raise_()

    def get_settings_dict(self):

        settings_dict = {}

        if self.windowState() == QtCore.Qt.WindowMaximized:
            state = True
            if self.ui_settings_dict:
                settings_dict['pos'] = self.ui_settings_dict['pos']
                settings_dict['size'] = self.ui_settings_dict['size']
            else:
                settings_dict['pos'] = self.pos().toTuple()
                settings_dict['size'] = self.size().toTuple()
        else:
            state = False
            settings_dict['pos'] = self.pos().toTuple()
            settings_dict['size'] = self.size().toTuple()
        settings_dict['windowState'] = state

        if self.projects_docks.keys():
            settings_dict['opened_projects'] = self.projects_docks.keys()
            if env_inst.get_current_project():
                settings_dict['current_active_project'] = str(env_inst.get_current_project())
        else:
            settings_dict['opened_projects'] = ''
            settings_dict['current_active_project'] = ''

        return settings_dict

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'pos': self.pos().toTuple(),
                'size': self.size().toTuple(),
                'windowState': False,
                'opened_projects': '',
                'current_active_project': '',
            }

        self.move(settings_dict['pos'][0], settings_dict['pos'][1])
        self.resize(settings_dict['size'][0], settings_dict['size'][1])

        if settings_dict['windowState']:
            self.setWindowState(QtCore.Qt.WindowMaximized)

    def readSettings(self):
        self.ui_settings_dict = env_read_config(filename='ui_settings', unique_id='ui_main', long_abs_path=True)
        self.set_settings_from_dict(self.ui_settings_dict)

    def writeSettings(self):
        env_write_config(self.get_settings_dict(), filename='ui_settings', unique_id='ui_main', long_abs_path=True)

    def closeEvent(self, event):

        # Closing server api
        env_api.close_server(self)

        for dock in self.projects_docks.values():
            # project_code = dock.widget().project.get_code()
            dock.widget().close()
            dock.close()
            dock.deleteLater()
            del dock
            # env_inst.cleanup(project_code)

        self.writeSettings()

        event.accept()

    def query_projects_finished(self, result=None):
        if result:
            self.restore_opened_projects()
            self.fill_projects_to_menu()
            env_inst.ui_main.set_info_status_text('')

            self.execute_after_all_ui_started()

    def query_projects(self):
        env_inst.ui_main.set_info_status_text(
            '<span style=" font-size:8pt; color:#00ff00;">Getting projects</span>')

        def get_all_projects_and_logins_agent():
            return tc.get_all_projects_and_logins()

        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        projects_items_worker = gf.get_thread_worker(
            get_all_projects_and_logins_agent,
            env_inst.get_thread_pool('server_query/server_thread_pool'),
            result_func=self.query_projects_finished,
            error_func=gf.error_handle
        )
        projects_items_worker.start()

    # def closeEventExt(self, event):
    #     self.ext_window.deleteLater()
    #     event.accept()
